# Paquete contable mensual — "el cierre le llega solo al contador"

**Estado:** diseño aprobado, pendiente de plan de implementación
**Fecha:** 2026-09-07 · **Commit base:** `824a04e` · **Autor del diseño:** sesión de brainstorming

---

## Problem Statement

El dueño baja tres CSV sueltos cuando se acuerda, y se los manda al contador como puede. Los archivos no dicen de qué local son ni de qué período, no traen totales de control, y les faltan datos que el contador necesita. El resultado es que el contador transcribe a mano lo que el sistema ya tiene.

## Evidence

Estado actual verificado sobre `824a04e`:

- **Un solo endpoint de exportación:** `GET /api/v1/reports/export/{kind}.csv` (`app/presentation/api/v1/reports.py:88`), roles OWNER y MANAGER.
- **Tres archivos:** `ventas-por-dia.csv` (desde `sale_facts`), `gastos.csv` (desde `payments` OUTFLOW confirmados), `libro-iva-ventas.csv` (desde `invoices` AUTHORIZED).
- **El formato CSV ya está bien resuelto:** delimitador `;`, CRLF, UTF-8 con BOM, decimales con coma (`app/presentation/csv_export.py`). Abre limpio en Excel-AR. **No se toca.**
- **`gastos.csv` descarta un dato que ya existe:** `PaymentORM.counterparty` (proveedor) está en la tabla y el export ni lo selecciona (`app/infrastructure/persistence/report_export_repo.py:78-84`).
- **Ningún archivo se autoidentifica:** sin razón social, sin CUIT, sin período, ni en el contenido ni en el nombre.
- **Sin totales de control:** el contador no tiene con qué validar que la carga entró completa.
- **Las horas del personal no salen en CSV:** `GetStaffReport` existe pero sólo devuelve JSON por API.
- **El arqueo de caja no se exporta.**
- **El monotributista recibe lo mismo que el RI**, aunque no presenta Libro de IVA.

## Proposed Solution

Un **paquete mensual** que se arma solo y le llega por mail al contador el primer día de cada mes, como ZIP adjunto. Adentro: una portada que identifica y totaliza, más los archivos del período, con nombres autoexplicativos.

## Key Hypothesis

Si el contador recibe el mes cerrado, identificado y totalizado sin pedirlo, deja de transcribir y el local deja de depender de que alguien se acuerde de mandarlo.

## What We're NOT Building

Decisiones tomadas explícitamente en el brainstorming. **No están en alcance:**

- ❌ **Libro de IVA Compras.** Requiere que el local cargue CUIT del proveedor, tipo y número de comprobante, y neto/IVA discriminado en cada factura. Es trabajo de carga diaria y una pantalla nueva. Se pospone; las compras siguen cargándose donde se cargan hoy.
- ❌ **Formato TXT importable a ARCA.** El Libro IVA Digital (RG 4597/2019) importa TXT de ancho fijo, dos archivos por régimen (comprobantes + alícuotas), encoding ISO-8859-1. El layout exacto está en un PDF escaneado de ARCA que no se pudo leer automáticamente. Queda como fase posterior, y **antes hay que extraer el layout a mano**.
- ❌ **Rol de contador con acceso propio al sistema.** Se descartó a favor del envío por mail.
- ❌ **Almacenamiento de objetos externo (S3/R2).** Se guarda en Postgres detrás de un port, para poder migrar después sin tocar casos de uso.
- ❌ **Retenciones y percepciones sufridas.** No hay datos hoy.
- ❌ **Conciliación bancaria automática.** Se entrega el detalle para conciliar, no la conciliación.

## Success Metrics

- El contador recibe el paquete del mes anterior sin intervención humana.
- Los totales de la portada cuadran con la suma de cada archivo.
- Un reenvío entrega el mismo binario que se mandó originalmente.
- Cero envíos duplicados del mismo período al mismo destinatario.

## Users & Context

- **Contador externo** (no es usuario del sistema): recibe un mail al mes. No tiene cuenta, no entra a la app.
- **Dueño / encargado** (OWNER, MANAGER): configura el mail del contador, prende el envío automático, consulta el historial y reenvía.
- **Condición fiscal:** el paquete se adapta a Responsable Inscripto y a Monotributo. Ambos desde el arranque.

---

## ✅ Bloqueante RESUELTO (2026-09-10)

**Este PRD nació bloqueado por el hallazgo H1 y ya no lo está.** Arreglado en
`bac3c54`, con el guard de anuladas cubierto en `639ced1`.

Lo que decía el bloqueo: `ventas-por-dia` lee `sale_facts`, la proyección cortaba
si la comanda no estaba `PAID`, y el autoservicio prepago deliberadamente nunca
llega a ese estado → las ventas del canal QR prepago no habrían llegado al
paquete del contador. Eso afectaba de forma crítica al `resumen-facturacion.csv`
del monotributista, que se calcula sobre `sale_facts` justamente para incluir lo
no facturado.

**Ahora la proyección pregunta si la plata está** (cobros confirmados que cubren
el total), no en qué punto del ciclo quedó la mesa. Verificado por mutación: con
el comportamiento viejo, el test del prepago da 0 ventas.

Detalle en `docs/audits/2026-09-05-auditoria-circuito-cobro-qr.md` (H1 y H5).

**Salvedad, no bloqueante:** el arreglo vale hacia adelante. Las ventas prepagas
anteriores a `bac3c54` que nunca se proyectaron seguirían faltando, y el
recálculo de `sale_facts` no las alcanza porque recorre solo comandas `PAID`. Hoy
es irrelevante — había una sola orden prepaga en la historia y estaba cancelada —
pero si alguna vez se prende el prepago y después hace falta historia previa, hay
que hacer un backfill aparte.

---

### Revisión de diseño (2026-09-10) — tres cosas a corregir antes del plan

**1 · El link de descarga no le sirve al contador.** El fallback por tamaño manda
un link, pero `GET /accounting/deliveries/{id}/download` está detrás de
OWNER/MANAGER y este mismo PRD dice que el contador **no tiene cuenta**. Se come
un 401. El patrón para resolverlo ya está en el repo: el token firmado de la
carta QR (`TableQrToken`, a su vez calcado de `hmac_presence`) — un link
stateless que no habilita nada más que bajar ese paquete. Resuelve además la
pregunta abierta #4: el vencimiento es el TTL del token.

**2 · Los totales de la portada NO van a cuadrar entre sí, y está bien.**
`ventas-por-dia` sale de `sale_facts` (devengado) y `cobros-conciliacion` de
`payments` (percibido). Son los dos libros distintos, y difieren por buenos
motivos: una comanda servida sin cobrar, un reembolso, la propina. Si la portada
los presenta juntos como "totales de control" sin decir de qué base es cada uno,
el contador va a perseguir una diferencia fantasma todos los meses — que es
exactamente el trabajo manual que este PRD viene a eliminar. **La portada tiene
que nombrar la base de cada total.**

**3 · Falta la columna de propina en `cobros-conciliacion.csv`.** Desde `bac3c54`
la comisión se estima sobre venta + propina (hallazgo H4), así que
`comisión / bruto` le daría al contador una tasa que no es la pactada. Y hay una
razón contable más fuerte: la propina **no es ingreso del local**, es plata de
terceros que pasa por la cuenta. Sin separarla, se registra como venta.

**Además, dos preguntas abiertas se pueden cerrar sin decidir nada nuevo:** la #1
y la #3 (cuándo corre el cron, quién lo configura) desaparecen si la corrida
mensual se cuelga del worker que ya corre en el proceso (el outbox de la Fase 4
de escalabilidad). Ya itera por intervalo y ya tiene la forma que este PRD pide
—recorrer locales, que una falla no aborte la corrida—. Con varias réplicas
correría N veces, pero la restricción de unicidad `(tenant, período)` que el PRD
ya define lo bloquea sola.

**Sugerencia de alcance:** las fases 0–2 dejan el paquete armado y descargable a
mano, y ahí está casi todo el valor — el dueño ya reemplaza tres CSV sueltos por
un ZIP identificado y completo. Las fases 3–5 (guardar, mail con adjunto, cron,
purga) automatizan el último tramo: tres tablas, un puerto de mail nuevo y un job
mensual para ahorrar un mail por mes. Conviene cortar en la fase 2, ponerlo en
manos de un contador de verdad, y automatizar con esa devolución en la mano.

---

## Solution Detail

### Contenido del ZIP

Nombre del paquete: `<AAAA-MM>_cierre-contable_<CUIT>.zip`
Nombre de cada archivo: `<AAAA-MM>_<contenido>_<CUIT>.csv`

| Archivo | Contenido | Fuente | Estado |
|---|---|---|---|
| `portada.txt` | Razón social, CUIT, condición fiscal, período, inventario de archivos y totales de control | — | Nuevo |
| `libro-iva-ventas.csv` | Sólo RI. Comprobantes autorizados: fecha, tipo, PV, número, doc receptor, neto, IVA, total, CAE | `invoices` | Existe |
| `resumen-facturacion.csv` | Sólo Monotributo. Facturado del período + acumulado 12 meses móviles, para control de categoría | `sale_facts` (ver nota) | Nuevo |
| `ventas-por-dia.csv` | Fecha, órdenes, unidades, ventas, costo de insumos, **+ desglose por medio de cobro** | `sale_facts` + `payments` | Ampliar |
| `gastos.csv` | Fecha, rubro, **proveedor**, medio, monto, detalle | `payments` OUTFLOW | Ampliar |
| `personal-horas.csv` | Por empleado: horas trabajadas, extras, propinas cobradas, valor hora | `shifts`, `users`, `payments` | Nuevo |
| `caja-arqueo.csv` | Por cierre: fecha, esperado y contado por método, diferencia | `cash_sessions`, `cash_counts` | Nuevo |
| `cobros-conciliacion.csv` | Por cobro: fecha, método, bruto, comisión, neto acreditado, referencia externa | `payments` | Nuevo |

**Nota sobre el resumen de monotributo.** La fuente es `sale_facts`, **no** `invoices`. Un monotributista puede facturar a mano y no tener ningún comprobante electrónico cargado; si el acumulado se calculara desde `invoices`, le daría cero y el control de categoría sería inútil. `sale_facts` tiene todas las ventas, estén facturadas o no — que es exactamente lo que mide el límite de categoría. **Esto hace que el archivo dependa de H1 de forma crítica.**

### Reglas de formato (no negociables)

1. **Los CSV quedan limpios.** Fila 1 = encabezados, resto = datos. **Nada más.** Un bloque de identificación arriba rompe Excel y rompe cualquier importador.
2. **La identificación y los totales van sólo en `portada.txt`.** Un único lugar donde el contador verifica.
3. **Se reusa `csv_export.py` tal cual está.** `;`, CRLF, UTF-8 con BOM, decimales con coma.
4. **Los importes siguen siendo enteros de unidad mínima** en todo el backend; el formateo a decimal AR ocurre sólo en la capa de export (`_ar()`).

### User Flow (camino crítico)

1. El dueño carga el mail del contador y prende el envío automático (una sola vez).
2. El día 1 de cada mes, un cron externo golpea el endpoint de la corrida mensual.
3. El sistema recorre los locales con envío prendido que todavía no recibieron el período anterior.
4. Por cada uno: arma los archivos → comprime → guarda el ZIP → manda el mail con adjunto → registra el envío.
5. Si un local falla, **se registra el fallo y la corrida sigue** con el siguiente.
6. El dueño ve el historial y puede reenviar.

---

## Technical Approach

Clean Architecture, según `docs/architecture/backend-clean-architecture.md`. Backend 100% en inglés.

### `domain/accounting/` (nuevo)

| Pieza | Responsabilidad |
|---|---|
| `value_objects.py` | `FiscalPeriod` (año, mes): parseo, rango de fechas UTC, etiqueta, período anterior. Matemática pura de calendario. `DeliveryStatus` (PENDING / SENT / FAILED). `ControlTotals`. |
| `entities.py` | `AccountantDelivery`: período, destinatario, estado, totales, `sent_at`, referencia al paquete guardado, último error. |
| `settings.py` | `AccountingSettings` + `AccountingSettingsRepository`. **Calca el patrón de `domain/payment/self_pay_settings.py`**: dataclass congelada + puerto con `get`/`update`. Campos: `accountant_email`, `auto_send_enabled`. |
| `repository.py` | `AccountantDeliveryRepository`. |
| `ports.py` | `PackageStore` (guardar / traer / borrar bytes). `DocumentEmailSender`. |

### `application/reporting/` (amplía lo existente)

| Caso de uso | Responsabilidad |
|---|---|
| `BuildAccountantPackage` | Llama a los read models según condición fiscal, arma los archivos y la portada. **No sabe de ZIP ni de mail.** Devuelve `PackageContents`. |
| `SendAccountantPackage` | Construir → comprimir → guardar → mandar → registrar. Un solo local. |
| `RunMonthlyDeliveries` | Entrada del cron. Recorre los locales elegibles. **Una falla no aborta la corrida** — mismo criterio que `ReportPendingTaxSales` (`app/application/tax/reporting.py`). |
| `ResendAccountantPackage` | Recupera el binario guardado y lo remanda. No regenera. |
| `to_zip(files) -> bytes` | Función pura sobre `zipfile` de stdlib. **Sin puerto**: no es un servicio externo. |

Read models nuevos, siguiendo `ReportExportReadModel`: `LaborExportReadModel`, `CashReconciliationReadModel`, `MonotributoSummaryReadModel`.

### `infrastructure/`

- `persistence/accounting_repo.py` — delivery repo + settings repo.
- `persistence/package_store.py` — adaptador Postgres (`LargeBinary`).
- `persistence/report_export_repo.py` — ampliar: agregar `counterparty` a gastos, medio de cobro a ventas, y los tres read models nuevos.
- `email/` — los tres adaptadores (console, resend, smtp) implementan `DocumentEmailSender`, reusando el transporte que ya tienen.

### `presentation/api/v1/accounting.py` (nuevo)

| Endpoint | Rol | Para qué |
|---|---|---|
| `GET/PUT /accounting/settings` | OWNER | Mail del contador, envío automático |
| `POST /accounting/deliveries` | OWNER, MANAGER | Envío manual de un período |
| `GET /accounting/deliveries` | OWNER, MANAGER | Historial |
| `GET /accounting/deliveries/{id}/download` | OWNER, MANAGER | Bajar el ZIP guardado |
| `POST /accounting/deliveries/{id}/resend` | OWNER | Reenviar |
| `POST /platform/jobs/monthly-accounting` | Plataforma | Disparador del cron |

El endpoint del cron va bajo **autenticación de plataforma**, no de local: la corrida es sobre todos los tenants. Sigue el patrón que ya existe en `api/v1/platform.py`.

### Decisiones de diseño marcadas

**1 · Identidad fiscal al tenant, no a los settings contables.**
Hoy el CUIT vive sólo en `tax_credentials`, que existe únicamente si configuraron facturación electrónica. Un monotributista que factura a mano no tiene CUIT en ningún lado, y la portada lo necesita.
→ `legal_name` y `cuit` van a `TenantORM` (son identidad del negocio, no del feature). Migración con backfill desde `tax_credentials` donde ya existan. `tax_credentials` conserva su propio CUIT para AFIP.

**2 · Puerto de mail nuevo, no extender `EmailSender`.**
`EmailSender` vive en `domain/identity/ports.py` y sus tres métodos son de autenticación (verificación, reset, invitación), todos con `link`, ninguno con adjunto. Meterle "mandá el paquete contable" mezcla límites de contexto.
→ `DocumentEmailSender` aparte, en `domain/accounting/ports.py`.

**3 · Se guarda el binario Y el registro (opciones B+C del brainstorming).**
Postgres detrás de `PackageStore`. Dos guardas:
- **Tope de tamaño.** Si el paquete lo supera, el mail sale con link de descarga en vez de adjunto. El paquete se guarda igual. Evita rebotes.
- **Retención de 24 meses.** Los paquetes viejos se borran solos.

El registro guarda además los **totales de control del momento del envío**. Si alguien corrige datos de un período ya cerrado, el sistema puede mostrar la diferencia entre lo enviado y lo actual — el dueño se entera de que su contador tiene números viejos.

---

## Data Model

### Tabla nueva: `accounting_settings`

Una fila por tenant. Patrón idéntico a `self_pay_settings`.

| Columna | Tipo | Nota |
|---|---|---|
| `tenant_id` | UUID FK, único | |
| `accountant_email` | String(160) nullable | |
| `auto_send_enabled` | Boolean | Default `false` |

### Tabla nueva: `accountant_deliveries`

| Columna | Tipo | Nota |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID FK, index | RLS |
| `period_year`, `period_month` | Integer | Único junto a `tenant_id` → sin duplicados |
| `recipient_email` | String(160) | Congelado al enviar |
| `status` | String(20) | PENDING / SENT / FAILED |
| `control_totals` | JSONB | Testigo de lo enviado |
| `package_id` | UUID nullable FK | |
| `sent_at`, `created_at` | Timestamptz | |
| `error` | String nullable | Último fallo |

### Tabla nueva: `accountant_packages`

| Columna | Tipo | Nota |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID FK, index | RLS |
| `content` | LargeBinary | El ZIP |
| `size_bytes` | Integer | |
| `created_at` | Timestamptz | Para la purga a 24 meses |

### Cambio a `tenants`

Agregar `legal_name` (String(160), nullable) y `cuit` (String(13), nullable). Migración con backfill desde `tax_credentials`.

**Todas las tablas nuevas llevan RLS y filtro explícito por `tenant_id`.**

---

## Error Handling

| Situación | Comportamiento |
|---|---|
| Un local falla en la corrida mensual | Se registra FAILED con el error, la corrida sigue con el siguiente. Reintentable. |
| Falta el mail del contador | El local no es elegible. No es error: se saltea. |
| Falta CUIT o razón social | Falla con error claro. La portada no puede armarse sin identificación. |
| El paquete supera el tope de tamaño | Se guarda igual, el mail sale con link en vez de adjunto. |
| El proveedor de mail rechaza | FAILED con el error del proveedor. El paquete queda guardado, reenviable. |
| Período ya enviado | La restricción de unicidad lo bloquea. Reenviar es una operación explícita distinta. |
| Período sin movimiento | Se manda igual, con totales en cero. El contador necesita saber que no hubo actividad. |

---

## Testing

Cobertura exigida por `CLAUDE.md`: **80%+ en dominio y casos de uso.**

**Unitarios de dominio** — `FiscalPeriod` (rangos, bordes de mes, año nuevo), transiciones de `AccountantDelivery`, `ControlTotals`.

**Unitarios de casos de uso, con fakes por DI** — armado del paquete para RI vs Monotributo; que una falla no aborte la corrida mensual; idempotencia por período; fallback a link cuando se supera el tope; reenvío entregando el mismo binario.

**Integración** — el ZIP contiene los archivos esperados y los totales de la portada cuadran con la suma de cada CSV; el paquete de un monotributista no trae libro de IVA; los CSV abren correctamente con el formato de `csv_export.py`.

---

## Implementation Phases

Sugerencia de corte. El plan detallado se escribe aparte con `/prp-plan`.

| Fase | Contenido | Depende de |
|---|---|---|
| **0** | `FiscalPeriod` + identidad fiscal en tenant + migración con backfill | — |
| **1** | Read models nuevos (personal, caja, conciliación, monotributo) + arreglos a los existentes (proveedor, medio de cobro) | 0 |
| **2** | `BuildAccountantPackage` + portada + `to_zip` + endpoint de descarga manual | 1 |
| **3** | `PackageStore` + `accountant_deliveries` + historial + reenvío | 2 |
| **4** | `DocumentEmailSender` en los tres adaptadores + envío con adjunto | 3 |
| **5** | `AccountingSettings` + `RunMonthlyDeliveries` + endpoint de plataforma + purga a 24 meses | 4 |

Las fases 0 y 1 son paralelizables con el arreglo de H1.

---

## Decisions Log

| Decisión | Elegido | Descartado |
|---|---|---|
| Condición fiscal | RI y Monotributo desde el arranque | Uno primero |
| Entrega | Mail automático mensual | Descarga manual · Acceso propio del contador |
| Qué recibe el contador | ZIP adjunto (con fallback a link por tamaño) | Sólo link · Adjunto chico + link |
| Lado compras | Fuera de alcance por ahora | Compras completas · Compras opcionales en dos niveles |
| Formato del libro de ventas | CSV mejorado, legible y verificable | TXT ARCA · Ambos · Consultar al contador primero |
| Contenido del ZIP | Los cuatro bloques (fiscal, gestión, laboral, caja) | Subconjuntos |
| Persistencia | Guardar binario **y** registro (B+C) | Sin guardar nada · Sólo registro |
| Ubicación del binario | Postgres detrás de `PackageStore` | S3/R2 · Filesystem |
| Identidad fiscal | En `tenants` | En `accounting_settings` |
| Puerto de mail | `DocumentEmailSender` nuevo | Extender `EmailSender` |

---

## Research Summary

**Libro IVA Digital (ARCA)** — RG 4597/2019, modificada por RG 5133/2021. Obligatorio para Responsables Inscriptos y sujetos exentos; reemplazó los libros de IVA en papel desde 2020. Su importación usa **dos archivos por régimen** (comprobantes + alícuotas), en **TXT de ancho fijo** con el mismo layout del viejo régimen CITI, encoding ASCII / ISO-8859-1 / Windows-1252. Categorías separadas: ventas, compras, compras de importación, bienes usados. Novedad 2026: se pueden importar los importes en pesos.

**Limitación de la investigación:** el layout campo por campo no se pudo verificar. El PDF oficial de especificaciones de ARCA es un escaneo de imágenes sin texto extraíble. **Si en el futuro se implementa el TXT importable, ese layout hay que extraerlo a mano del PDF oficial antes de codear.**

Fuentes:
- [Especificaciones Libro IVA Digital — AFIP/ARCA (PDF, rev. 30/07/2025)](https://www.afip.gob.ar/iva/documentos/Libro-IVA-Digital-Especificaciones.pdf)
- [Novedades IVA — ARCA](https://arca.gob.ar/iva/sujetos-exentos/novedades.asp)
- [Libro IVA Digital LID — SOS Contador](https://ayuda.sos-contador.com.ar/menu-asistentes-arca/libro-iva-digital-lid)

---

## Open Questions

1. **Día y hora exactos de la corrida mensual.** Propuesto: día 1. Definir el huso y qué pasa si el cron externo no corre.
2. **Tope de tamaño concreto** para el fallback a link. Propuesto: 10 MB, a validar contra el límite del proveedor de mail.
3. **Quién configura el cron externo** y en qué plataforma de deploy.
4. **Vencimiento del link de descarga** en el caso de fallback.
5. **Copia al dueño.** ¿El mail va sólo al contador o con copia al OWNER?

---

## Próximo paso

Escribir el plan de implementación con `/prp-plan` sobre este PRD, cortando por las fases de arriba.

H1 ya está arreglado (`bac3c54`), así que el envío automático no tiene bloqueantes. Incorporar al plan las tres correcciones de la revisión de diseño de arriba.
