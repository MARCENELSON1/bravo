# Prior art "Nacional" → qué reutilizar en BRAVO/Wellnod

**Fecha:** 2026-07-04 · **Fuente:** `~/Desktop/nacional/recuperado/` — ERP argentino (Java Swing + MariaDB) que **el propio usuario desarrolló hace años**, perdió el código, recuperó el ejecutable y descompiló (jadx + yGuard). **Autoría propia → reutilizable sin problema legal.** No se porta código (Java 8 descompilado/ofuscado, stack equivocado): se extrae el **conocimiento de dominio y las decisiones ya validadas en producción** para el Build de BRAVO.

Analizado con 5 agentes en paralelo: facturación electrónica AFIP, IVA/impuestos, modelo de datos (`master.sql`, 324 tablas), ventas/precios/stock, y compras/caja/contabilidad.

---

## TL;DR — ranking de valor para BRAVO

| # | Activo | Valor | Dónde |
|---|---|---|---|
| 1 | **Adapter AFIP completo (WSAA + WSFEv1 + CAE)** | 🔥 Altísimo — es el diferenciador "AFIP nativo", aún NO construido | `WebServiceAFIPImpl.java` (1734 líneas, fuente completa) + `fe.jar` |
| 2 | **Catálogos/seeds fiscales AFIP** (códigos comprobante, condición IVA, tipo doc, tributos, alícuotas) | 🔥 Alto — copiables casi tal cual como datos de referencia | `master.sql` (`fac_tipo_afip`, `bas_condicion_iva`, `vta_fe_tributo`) + `TipoAFIP`/`CondicionIVA` |
| 3 | **Modelo fiscal del comprobante** (snapshot receptor, líneas de impuesto, desglose neto/IVA/percepciones, CAE) | 🔥 Alto — diseño del domain `Invoicing`/`Tax` | `vta_comprobante*`, `iva_comprobante`, `ImpuestoDeComprobante` |
| 4 | **Fórmulas de cálculo de IVA por ítem + desglose** (IVA incluido/excluido, redondeos) | Alto — portables literal a Python/Decimal | `ComprobanteForm.calcularImporteItem`, `ComprobanteServiceImpl.calcularComprobante` |
| 5 | **Recepción de mercadería con costo real** → food cost fiel | Medio-alto — mejora directa del Asesor | `mod_compra` (`StockDeComprobanteDAO`, `ItemDeProveedor`) |
| 6 | **Listas de precios + combos + descuentos** | Medio — features de producto (menús, happy hour, delivery) | `Lista`/`Precio`/`Combo`/`ItemDeCombo` |
| 7 | **Recetas multinivel (BOM en árbol)** | Medio — hoy BRAVO tiene receta plana | `FormulaItem` (árbol recursivo) |
| 8 | **Arqueo de caja por medio de pago** | Medio — evolución del arqueo Z actual | `CajaModalidad` (`ajusteCaja` por tender) |
| 9 | Mapeo documento→Libro IVA/DDJJ + saldo técnico | Medio — insumo del copiloto/contador | `DeclaracionJuradaIVADAO` |
| 10 | Centros de costo / prorrateo por área | Bajo-medio — inspiración para márgenes por área | `CentroDeCosto`/`MovimientoDeCosto` |

**Regla transversal:** el 90% del valor está en la **capa fiscal AFIP** (catálogos, matriz condición IVA→letra, desglose de impuestos, CAE, certificado, punto de venta). El motor operativo/comercial de Nacional es un ERP retail/industrial monolítico de escritorio — mayormente **no** aplica a un SaaS multi-tenant de hospitality.

---

## 1. Facturación electrónica AFIP (el activo #1)

Fuente clave: `fuentes/server/lib/mod_base/sources/ns/nacional/base/WebServiceAFIPImpl.java` (adapter, fuente jadx **completa**, sin "method not decompiled") + `WebServiceAFIP.java` (port) + `fe.jar` (`_extraido/server/lib/ext/fe.jar`, 1555 clases, solo bytecode: wrappers `ns.ws.*` + stubs AFIP autogenerados + WSAA + firma CMS BouncyCastle).

### Web services cubiertos
| WS | Endpoint prod / homolog | Para qué |
|---|---|---|
| **WSAA** (auth) | `wsaa.afip.gov.ar/ws/services/LoginCms` / `wsaahomo…` | Login CMS → token+sign (TA) |
| **WSFEv1** (mercado interno) | `servicios1.afip.gov.ar/wsfev1/service.asmx` / `wswhomo…` | CAE de Factura/NC/ND A/B/C |
| **WSFEXv1** (exportación) | `…/wsfexv1/service.asmx` | Factura E |
| **WSFECRED/FCE** (crédito MiPyME) | namespace `ar.gob.afip.wsfecred` | Aceptar/rechazar FCE |
| **wsmtxca** (matrix, detalle ítem) | `serviciosjava.afip.gob.ar/wsmtxca/…` | CAE con detalle de artículos |
| **Padrón REST A5/A13** | `aws.afip.gov.ar/sr-padron/v2/persona/{cuit}` | Autocompletar razón social + condición IVA por CUIT (gratis, JSON) |

Operaciones WSFEv1 confirmadas: `FECAESolicitar`, `FECompUltimoAutorizado`, `FECompConsultar`, `FEParamGet{PtosVenta,TiposCbte,TiposConcepto,TiposDoc,TiposIva,TiposTributo,Cotizacion,…}`, y **`FEParamGetCondicionIvaReceptor`** (RG 5616 — actualizado a la normativa de condición IVA del receptor).

### Flujo WSAA (ticket de acceso) — a replicar
1. **Credenciales:** `.p12` (PKCS12 con clave privada + X509) + password + CUIT + flag ambiente (`PRODUCCION`/`PRUEBA`), por empresa. En BRAVO: storage cifrado del `.p12` **por tenant** (tabla `bas_certificado_digital` es el diseño exacto).
2. **TRA (LoginTicketRequest):** XML con `<uniqueId>`, `<generationTime>`, `<expirationTime>` (ventana ~12 h) y `<service>` = `wsfe`/`wsfex`/`wsfecred`/`wsmtxca`/`ws_sr_constancia_inscripcion`.
3. **Firma CMS:** BouncyCastle, `CMSSignedDataGenerator` SHA1 detached=false → Base64. (En Python: `cryptography`/OpenSSL PKCS7; AFIP hoy acepta SHA256.)
4. **LoginCMS** → parsea `<token>`, `<sign>`, `<expirationTime>`.
5. **Caché del TA (clave):** map por `tenant_id` (Nacional: `database+"_"+empresaId`), un TA por `service`. **Reutiliza el TA hasta 10 h** (`isExpired()` = `diffHours ≥ 10`, margen bajo los 12 h de AFIP); re-login lazy. Avisa si el **certificado** vence en ≤30 días.
6. **Robustez:** reintento ×3 ante `ConnectionException`; detecta "certificado expirado", "computador no autorizado", "TA ya vigente/duplicado", **desfasaje de reloj vs `time.afip.gov.ar`**, HTTP 5xx → "probá en una hora".

### Flujo de autorización (solicitud de CAE) — a replicar
Builder `getComprobanteElectronico(Factura)` (líneas 765-940). Campos del request `FEDetRequest` (nombres AFIP exactos, ahorra leer los manuales):
- `concepto`: **PRODUCTO=1, SERVICIO=2, PRODSERV=3** (BIENDEUSO→1, LOCACION→2).
- **Documento receptor:** sin doc → `docTipo 99` (CF, sin nº); DNI → `96`; si no → **`80` (CUIT)**. **Edge case:** CUITs genéricos `30111111118`/`11111111113` → forzar `99`.
- **`condicionIVAReceptorId`** (RG 5616): `condicionIVA.idFE`, **default 5 (Consumidor Final)**.
- Numeración: **`FECompUltimoAutorizado(ptoVta, cbteTipo) + 1`**, con `CbteDesde = CbteHasta`.
- Importes: `impTotal`, `impTotConc` (= **no gravado**), `impNeto`, `impOpEx` (= **exento**), `impTrib`, `impIVA`. (Nomenclatura AFIP no obvia — anotada.)
- Moneda: `monId="PES"` ⇒ `monCotiz=1`; extranjera ⇒ cotización de `FEParamGetCotizacion` + `canMisMonExt="S"`.
- **`AlicIva[]`** (solo si `neto>0`): por alícuota, `Alicuota(TipoIVA, baseImp=neto, importe=iva)`; 0% se envía igual (importe 0).
- **`Tributo[]`** (percepciones no-IVA con importe>0): `baseImp = importe/(alic/100)`.
- **`CbteAsoc[]`** (NC/ND): tipo, ptoVta, número, CUIT emisor, fecha del original.
- **`Opcional[]`** FCE: CBU→`"2101"`, Alias→`"2102"`, TipoTransferencia→`"27"`.
- Fechas de servicio (`fchServDesde/Hasta/VtoPago`) solo para concepto 2/3.

**Respuesta:** `Resultado` **"A"=APROBADO / "P"=PARCIAL / "R"=RECHAZADO**; guardar `CAE`, `CAEFchVto` (yyyymmdd), `Obs[]` (aprobado-con-observaciones) separado de `Err[]` (rechazo → excepción).

### Mapa alícuota IVA → id AFIP (`TipoIVA`, confirmado en bytecode)
`3=0% · 4=10.5% · 5=21% · 6=27% · 8=5% · 9=2.5%`. Gastronomía = **21%**.

### Códigos de comprobante AFIP (`TipoAFIP`)
`1`=Factura A, `6`=B, `11`=C, `2/3`=ND/NC A, `7/8`=ND/NC B, `12/13`=ND/NC C, `19/20/21`=Factura/ND/NC E, `51`=M, `201/202/203`=FCE A ND/NC, `81`=Tique Factura A. El catálogo completo (~90 filas) está en `master.sql` tabla `fac_tipo_afip` → **seed directo del adapter**.

### Reutilización para BRAVO (Build)
Port `AfipInvoicingPort` (espejo de `WebServiceAFIP`): `authorizeInvoice(cbte)→CAE`, `getLastAuthorized(ptoVta, tipo)→nro`, `getPuntosDeVenta()`, `getCotizacion(moneda)`, `getContribuyente(cuit)` — con fake para tests (misma separación que ya usa Nacional). WSAA como sub-servicio con caché de TA por tenant. **En Python: consumir los WSDL con `zeep` guiándose por los nombres de operación/campo documentados acá** (no portar los stubs de `fe.jar`). Padrón: usar el REST A5/A13 (más barato que el SOAP CI).

**Gaps:** el marshalling SOAP vive solo en bytecode; la matriz emisor×receptor→letra y los seeds `idFE`/`TipoAFIP` viven en la DB `sys_nacional` (MariaDB binaria, no extraíble por grep) → re-derivar de la normativa AFIP y validar. Certificados públicos embebidos en el código = del servicio gratuito CI, **no reutilizar**.

---

## 2. IVA / impuestos (domain `Tax`)

Fuente: `mod_iva` (134 archivos) + `mod_base/CondicionIVA.java`, `TipoDocumento.java`, `Rubro.java`.

- **Patrón data-driven (clave):** el impuesto es una **entidad configurable con fórmula**, no un enum hardcodeado. `Impuesto{tipo, alicuota, formulaAlicuota, formulaImporte, calculo, provincia, tributoFE, idAFIP, ddjjIVA, aplicacion}`. Esto es lo que da "AFIP nativo" multi-jurisdicción sin recompilar. Para BRAVO: `Tax`/`TaxRate` como catálogo con `afip_code`; empezar simple (base+rate+min+jurisdiction), sin motor de expresiones completo.
- **Condiciones de IVA** (`CondicionIVA`, catálogo con `idFE`): RI, Monotributo (RM), Exento, Consumidor Final (CF), No Categorizado (NC). Códigos AFIP RG 5616: 1=RI, 4=Exento, 5=CF, 6=Monotributo, 7=No Cat. Se **snapshotea** en el comprobante.
- **Tipos de documento AFIP:** CUIT=80, CUIL=86, DNI=96, Pasaporte=94, OTRO=99.
- **Fórmulas de IVA por ítem** (portables literal — el corazón de un ticket):
  - IVA **incluido** (caso gastronomía): `neto = precio×cant / (1 + alic/100)`; `iva = precio×cant − neto`.
  - IVA **excluido**: `neto = precio×cant`; `iva = neto × alic/100`.
  - `alic == 0` → iva = 0. Intermedios a 4 decimales, importe final a 2.
- **Desglose del comprobante** (`calcularComprobante`): acumula por `Impuesto.Tipo` en `neto/exento/noGravado/iva/impuesto1..9`; `subtotal = neto+exento+noGravado`; `total = Σ importes no-AUXILIAR` (líneas AUXILIAR no suman); `alicuotas` = lista de alícuotas NETO distintas.
- **Percepciones/retenciones** (B2B, diferible en MVP): percepciones dentro del comprobante (`IMPUESTO_1..9`), retenciones al pago (`Certificado{imponible, alicuota, retenido, regimen}`), IIBB por provincia (`ConvenioMultilateral` con coeficiente). **No hardcodear**: modelar con jurisdicción + regla.
- **Libro IVA / DDJJ** (insumo del copiloto "¿cuánto IVA debo?"): clasificación `modulo(COMPRA/VENTA) × documento(FACTURA/NC/ND) × saldo(SUMA/RESTA) × tipo(NETO/EXENTO/IVA)`. NC resta, FA/ND suma. Saldo técnico = `totalVentas − totalCompras`; a pagar si > pagos a cuenta (retenciones+percepciones+saldo libre anterior).

**Checklist fiscal AR ya resuelto (que no se olvide al construir `Invoicing`):** snapshot del receptor congelado · CUIT cliente ≠ CUIT empresa · documento+signo para libros · letra ≠ tipo · CAE+vencimiento · concepto AFIP (producto/servicio exige fechas de servicio) · anulación por flag (no borrado, integridad de numeración) · período mensual para libros · prorrateo de IVA para actividad mixta.

---

## 3. Modelo de datos (`master.sql`, 324 tablas) → mapeo a BRAVO

| Concepto Nacional | Tabla(s) | Equivalente BRAVO | Gap a cubrir |
|---|---|---|---|
| Comprobante cabecera | `vta_comprobante` | `Invoice` (fiscal, ≠ `Order` operativo) | `cae`, `cae_expiration`, `resultado`, `punto_venta`, `tipo_afip`, `letra`, **snapshot fiscal del receptor** |
| Detalle | `vta_comprobante_item` | `OrderItem`/`InvoiceItem` | `alicuota`/`iva` por línea |
| **Líneas de impuesto** | **`vta_comprobante_impuesto`** (1 fila por concepto/alícuota) | (no existe) | Crear `InvoiceTaxLine` — patrón fila-por-alícuota, NO columnas fijas |
| Catálogo impuestos + tributos AFIP | `vta_impuesto`, `vta_fe_tributo` | parcial | `Tax` + seeds |
| Condición IVA + matriz letra | `bas_condicion_iva`, `vta_tipo_condicion_iva` | (no existe) | `IvaCondition` con código AFIP + regla de letra |
| Códigos AFIP comprobante | `fac_tipo_afip` (~90) | (no existe) | Seed directo |
| Cliente/receptor | `vta_cliente` (orientado a CF) | `Customer` | `condicion_iva`, `tipo_doc`/`nro_doc`, `numero_ib` |
| **Certificado AFIP** | **`bas_certificado_digital`** (`.p12` blob, password, cuit, `ambiente`) | (no existe) | Storage cifrado del `.p12` por tenant para WSAA |
| Punto de venta | `vta_punto_de_venta` (nro AFIP + `emision` + ambiente) | (no existe) | Entidad `PointOfSale` |
| Producto | `stk_item` | `Product` | unidad, barcode, alícuota vía lista |
| Insumo/receta | `stk_item` (MP/SE) + `stk_formula` | `Ingredient`+`Recipe` | cubierto (BRAVO plano vs árbol) |
| Lista/precio | `stk_lista`+`stk_precio` | `Product.price` (único) | listas múltiples (opcional) |
| Stock | `stk_existencia` (saldo) + `stk_lote` | `Inventory` | saldo + lote/vencimiento |
| Cobro | `vta_cobro` (desglose por medio) | `Payment` | multi-tender |
| Libro IVA | `iva_comprobante` (read-model fiscal) | (regenerable de `sale_facts`) | read-model DDJJ |

**Patrones a reutilizar:** (1) **snapshot fiscal del receptor** congelado en el comprobante; (2) **desglose como filas** (`InvoiceTaxLine`), no columnas `impuesto_1..9`; (3) **seeds AFIP** casi tal cual; (4) **separación operación (`vta_`) vs libro fiscal (`iva_`)** — encaja con el event-sourcing/`sale_facts` que BRAVO ya usa.

**NO copiar:** claves naturales compuestas (`'B 00001 00000001'` — BRAVO usa UUID+`tenant_id`); columnas fijas `impuesto_1..9`; tabla-motor `vta_tipo_comprobante` de ~80 flags; numeración atada a `hostname`; blobs en la DB; **multi-empresa por columna sin RLS** (BRAVO exige `tenant_id`+RLS por CLAUDE.md).

---

## 4. Ventas, precios y stock (features de producto)

Fuente: `mod_venta` (186) + `mod_stock` (179).

- **Listas de precios** (`Lista`/`Precio`) — el gap #1 de producto. Varias listas por canal (salón/delivery/happy-hour), cada una con modo markup (**ganancia** `×(1+g/100)` / **utilidad** `÷(1−u/100)` / precio fijo), flag IVA-incluido, regla de redondeo (paso + método ROUND/CEIL/FLOOR), qty-breaks, derivación madre/hija, y **antigüedad de precio** (`getDiasColor` = semáforo de insumo sin actualizar). BRAVO hoy: un solo `price: Money` por producto.
- **Combos/menús** (`Combo`/`ItemDeCombo`) — bundle nombrado con precio y descuento propios (mini-documento, no explosión en venta). Modelo directo de "menú del día = entrada+plato+bebida a $X". BRAVO no tiene combos.
- **Descuentos** en 3 niveles: ítem (`ajuste` %/$ con signo), documento (descuento global), lista. Descuentos compuestos: `1 − ∏(1+pᵢ/100)`. Con reparto neto/IVA. BRAVO no tiene descuentos (comps, 2x1, descuento de personal).
- **Recetas multinivel** (`FormulaItem`, árbol recursivo) — una salsa es una receta usada por un plato. `Item.isFormula()` marca elaborado; al vender/producir se consumen los componentes del stock. BRAVO `Recipe` es de un solo nivel.
- **Stock:** modelo de **saldo** (`stk_existencia`: cantidad/producción/comprometido por depósito) + flujo configurable por tipo de comprobante. **Valuación = on-hand × costo de lista** — **NO hay costeo por capas (PPP/PEPS)** en Nacional tampoco → si BRAVO quiere COGS exacto es construir de cero, no migrar. Coincide con el last-cost actual de BRAVO.
- **NO traer:** series/matriz talle-color, DSL de fórmulas, financiación en cuotas, multi-moneda, manufactura industrial.

---

## 5. Compras, caja y contabilidad

Fuente: `mod_compra` (139), `mod_fondo` (95), `mod_contabilidad` (84).

- **Recepción de mercadería con costo real** (`mod_compra`: `StockDeComprobanteDAO`, `ItemDeComprobante.precio`) → el food cost del Asesor deja de ser un número a mano y viene de comprobantes reales. **Traer como spec:** `GoodsReceipt` que actualiza stock y costo del `Ingredient`.
- **Lista de precios por proveedor** (`ItemDeProveedor`) → base para costo real y **alertas de suba de costos** (que el Asesor ya insinúa). **Traer.**
- **Cuenta corriente de proveedor** (`CtaCteProveedor`: saldo = compras − pagos). BRAVO tiene `Supplier` sin CC. **Traer.**
- **Arqueo por medio de pago** (`CajaModalidad`: inicial/entrada/salida/`ajusteCaja` **por tender** — efectivo/tarjeta/MP/CC). Es la evolución natural del arqueo Z de BRAVO (que hoy cuenta un total). **Traer como spec.** Extra: `Metal`/`CajaArqueo` = conteo por denominación (arqueo de efectivo asistido, opcional).
- **CC de cliente / fiado** (`CtaCteSaldo`) → encaja con Fase 12 CRM.
- **Centros de costo + prorrateo por %** (`CentroDeCosto`/`MovimientoDeCosto`) → **inspiración** para atribuir costos (labor, insumos) a áreas (cocina/salón/delivery) y sacar márgenes por área en el Asesor, sin asientos.
- **NO traer:** contabilidad de partida doble completa (`Asiento`/`Cuenta`/`Ejercicio`/ajuste por inflación) — overkill; el "Contador" (Fase 10) debe ser un **export/resumen** para el contador externo (ventas netas, IVA débito/crédito, compras, egresos), no un libro diario. Tampoco cheques/conciliación bancaria en MVP.

---

## 6. Recomendación / encaje en el roadmap

**El gran hallazgo:** ya resolviste AFIP en producción una vez. El `WebServiceAFIPImpl.java` es, en la práctica, **la especificación completa del adapter AFIP de BRAVO** — flujo WSAA con caché de TA, request de CAE campo por campo, edge cases (CUITs genéricos, no gravado vs exento, base del tributo), manejo de resultado/observaciones. Eso convierte la fase "AFIP nativo" de "investigar los manuales de AFIP desde cero" a "re-implementar en Python lo que ya diseñaste, validando contra la normativa vigente".

**Cuándo:** la fase Facturación/AFIP **no está en el foco inmediato** (hoy: Pantalla Finanzas D✅, siguen E/F). Cuando se decida arrancarla, este doc + los catálogos de `master.sql` son el punto de partida. Orden sugerido de un futuro plan AFIP:
1. Domain `Tax`/`IvaCondition` + seeds AFIP (catálogos de la sección 1/3).
2. `Invoice` fiscal (snapshot receptor + `InvoiceTaxLine` + CAE) separado del `Order` operativo.
3. Port `AfipInvoicingPort` + adapter WSAA/WSFEv1 con `zeep`, fake para tests, certificado `.p12` cifrado por tenant.
4. Selección de letra (matriz condición emisor×receptor) + numeración por punto de venta.

**Quick wins independientes de AFIP** (se pueden colar antes, si el negocio los pide): recepción de mercadería con costo real (mejora el food cost del Asesor), arqueo por medio de pago (mejora el cierre de caja), combos/menús y listas de precios (producto).

**Qué queda afuera para siempre (o casi):** partida doble, manufactura industrial, cheques de terceros, multi-moneda, matriz talle/color, el DSL de fórmulas. Son de un ERP retail/industrial; BRAVO es hospitality.
