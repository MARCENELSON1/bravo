# Plan: Fase 4 — Facturación electrónica AFIP (CAE)

## Summary
Cerrar el MVP vendible (operar → cobrar → **facturar**): emitir **comprobantes electrónicos** (Factura/NC/ND **A/B/C**) ante **AFIP/ARCA** y obtener el **CAE** (Código de Autorización Electrónico), sobre la Clean Arch + multi-tenant + `Money` ya existentes. **Build** (adapter propio, **reversible a Buy**) detrás de un port `ElectronicInvoicing`: autenticación **WSAA** (token+sign con certificado X.509 por CUIT) + **WSFEv1** (`FECompUltimoAutorizado` + `FECAESolicitar`). Es el diferenciador clave (AFIP nativo) y deja el dato fiscal limpio para el asesor (IVA, comprobantes).

> **DECISIÓN DE ALCANCE:** **Homologación primero** (entorno de testing de AFIP), luego producción por config. **Multi-tenant: cada local factura con SU CUIT + certificado** (credenciales por tenant, cifradas — **mismo patrón que Fase 3.5 MP OAuth**: `TokenCipher` + tabla cifrada + RLS). Emisión **monomoneda ARS** primero (el VO `Money` ya lo soporta). Tipos en alcance: **Factura A/B/C** + **Nota de Crédito/Débito A/B/C**. Fuera: exportación (E), FCE/MiPyME, percepciones, otros WS (padrón, constancia).

> **Prerrequisitos (los provee el usuario, por tenant):**
> 1. **CUIT** del emisor + **condición frente al IVA** (Responsable Inscripto / Monotributo) → define qué comprobante emite (A/B vs C).
> 2. **Certificado X.509 + clave privada** de AFIP (se genera un CSR, se sube a AFIP "Administración de Certificados Digitales", AFIP devuelve el `.crt`). Para **WSFE** hay que dar de alta el WS al certificado.
> 3. **Punto de venta** electrónico habilitado en AFIP (web services).
> 4. Entorno **homologación** primero (certificado de testing + WSDL de homologación).

## Estado de implementación
PENDIENTE. Depende de Fases 1→3 (✅ en `main`). Se implementa en rama `feat/fase-4-afip`. Roadmap: tras AFIP, el MVP (2+3+4) queda **vendible**.

## User Story
Como **dueño/encargado (OWNER/MANAGER)** quiero que, **al cobrar una comanda, pueda emitir su comprobante fiscal (A/B/C) y obtener el CAE de AFIP**, para **facturar legal en el mismo lugar donde opero y cobro**, sin pasar a otro sistema.

## Problem → Solution
Hoy la comanda se cobra (`PAID`) pero **no se factura**. → Sobre una comanda cobrada (o a demanda) se **emite un `Invoice`**: se calcula neto/IVA/total, se elige tipo (según condición del emisor y del receptor), se pide **CAE a AFIP** vía el port `ElectronicInvoicing` (adapter WSAA+WSFEv1), y el comprobante queda persistido con su CAE + vencimiento + número, tenant-scoped. Si AFIP rechaza (observaciones/errores), el `Invoice` queda en estado `REJECTED` con el detalle. Pasarelas/AFIP detrás del port → el dominio no conoce SOAP.

---

## Modelo de dominio (nuevo: `invoice`)
- **`Invoice`** (agregado): `id, tenant_id, order_id|None, type (InvoiceType), point_of_sale, number|None, doc_type (DocType), doc_number, concept, net: Money, vat: Money, total: Money, vat_breakdown: list[VatItem], status (InvoiceStatus), cae|None, cae_expiration|None, issued_at|None, rejection|None, created_at`.
- **VOs:**
  - `InvoiceType` (StrEnum): `FACTURA_A/B/C`, `NOTA_CREDITO_A/B/C`, `NOTA_DEBITO_A/B/C` (mapeo a códigos AFIP 1/6/11, 3/8/13, 2/7/12 en el adapter, no en el dominio).
  - `InvoiceStatus`: `DRAFT → AUTHORIZED (con CAE) | REJECTED`.
  - `DocType`: `CUIT/CUIL/DNI/CONSUMIDOR_FINAL` (códigos 80/86/96/99 en el adapter).
  - `VatItem`: `rate (Decimal/enum 21/10.5/27/0), base: Money, amount: Money`.
  - `Concept`: `PRODUCTOS/SERVICIOS/AMBOS`.
- **Reglas de tipo (en application, no en el adapter):** emisor RI → A (si receptor RI con CUIT) o B (consumidor final/monotributo); emisor Monotributo → C. Se deriva de la **condición fiscal del tenant** + datos del receptor.
- **IVA:** los precios de `Product` se tratan como **IVA incluido** (final) con alícuota por defecto **21%** (configurable por tenant/producto a futuro): `neto = total / 1.21`, `iva = total − neto`. Para comprobante **C** (monotributo) no se discrimina IVA (todo va como `ImpTotal`/no gravado según AFIP). Cálculo con enteros (minor units) — cuidar redondeo: AFIP valida `ImpTotal = ImpNeto + ImpIVA + ImpTotConc + ImpOpEx`.

## Integración AFIP (detalle técnico — consultar WSDL/manual de AFIP en implementación)
- **WSAA (auth):** armar **Login Ticket Request** (XML con `uniqueId`, `generationTime`, `expirationTime`, `service=wsfe`), firmarlo **CMS/PKCS#7** con el cert+clave del tenant, enviar a `LoginCms` → devuelve **`token` + `sign`** (TA) válido ~12 h. **Cachear el TA por (tenant, service)** y reusar hasta el `expirationTime` (AFIP **rate-limitea** los pedidos de TA). Firma CMS con `cryptography`/OpenSSL.
- **WSFEv1 (SOAP, `zeep`):**
  - **Auth header** en cada request: `{Token, Sign, Cuit}`.
  - `FECompUltimoAutorizado(ptoVta, cbteTipo)` → último número autorizado → `nro = último + 1`.
  - `FECAESolicitar(FeCAEReq)` con `FeCabReq{CantReg, PtoVta, CbteTipo}` + `FeDetReq[FECAEDetRequest]` (`Concepto, DocTipo, DocNro, CbteDesde/Hasta, CbteFch, ImpTotal, ImpTotConc, ImpNeto, ImpIVA, ImpOpEx, MonId='PES', MonCotiz=1, Iva[{Id, BaseImp, Importe}], CbteAsoc[] para NC/ND`). Respuesta: `FeCabResp.Resultado (A/R)`, `FeDetResp[{CAE, CAEFchVto, Resultado, Observaciones}]`, `Errors`. Mapear `A`→AUTHORIZED, `R`/Errors→REJECTED con el detalle.
  - `FEParamGet*` (tipos de comprobante/IVA/conceptos) → opcional, para validar catálogos.
- **Entornos:** homologación (`wswhomo`/`wsaahomo`) vs producción → URLs/WSDL por config + el `live_mode` de la credencial.
- **Fechas/formato:** `CbteFch` = `yyyymmdd`; importes con 2 decimales; numeración correlativa **sin huecos** por (ptoVta, tipo).

## Multi-tenant (credenciales fiscales por tenant)
- Tabla **`tax_credentials`** (mismo patrón que `payment_credentials` de Fase 3.5): `tenant_id, cuit, certificate (cifrado), private_key (cifrado), point_of_sale, fiscal_condition (RI/MONOTRIBUTO), live_mode, status`. Cifrado con el **`TokenCipher` (Fernet)** ya existente; **RLS** + filtro por `tenant_id`.
- El **TA de WSAA** se cachea por tenant (en memoria/DB con su `expirationTime`).
- La condición fiscal del tenant (RI/Monotributo) sale de acá (o se agrega a `Tenant`).

## Ports & Adapters
- **`ElectronicInvoicing` (port, domain/invoice/ports.py):**
  ```python
  @dataclass(frozen=True)
  class CaeResult:
      authorized: bool
      cae: str | None
      cae_expiration: date | None
      number: int | None
      observations: str | None
  class ElectronicInvoicing(ABC):
      @abstractmethod
      async def authorize(self, *, tenant_id: str, invoice: Invoice) -> CaeResult: ...
  ```
- **`AfipInvoicing` (infra):** WSAA (TA cache + CMS sign) + WSFEv1 (zeep). Lee las credenciales del tenant vía un `TaxCredentialsResolver` (descifra cert/key) — **espejo del `PaymentCredentialsResolver`**.
- **`FakeInvoicing` (dev/tests):** devuelve un CAE fijo + número incremental → permite testear todo el flujo **sin AFIP**. Selector `invoicing_provider` (afip|fake) en el container (como `email_sender`/`payment_gateway`).

---

## Mandatory Reading (moldes ya en el repo)
- **Fase 3.5 (credenciales por tenant):** `app/domain/payment/credentials.py`, `infrastructure/payments/credentials_resolver.py`, `infrastructure/security/fernet_cipher.py`, migración `0004_payment_credentials.py` (tabla cifrada + RLS) → **molde directo** para `tax_credentials`.
- **Fase 3 (pagos):** `domain/payment/{entities,ports}.py`, `application/payment/use_cases.py`, `presentation/api/v1/payments.py`, container Selector → molde de port + adapter + use case + API.
- **Money/IVA:** `domain/shared/money.py` (enteros + ISO-4217).
- **Persistencia/migración:** `0003_payments.py` (RLS), `models.py`, `mappers.py`.
- **Externo (consultar en implementación):** Manual WSFEv1 de AFIP/ARCA (códigos de comprobante, IVA, errores), WSDL de homologación. Evaluar `zeep` (SOAP) + `cryptography` (CMS) vs envolver una lib (`pyafipws`) detrás del port.

## Files to Change (estructura)
### Backend
| File | Acción |
|---|---|
| `app/domain/invoice/{__init__,entities,value_objects,exceptions,repository,ports}.py` | CREATE — `Invoice`, enums, errores, `InvoiceRepository`, `ElectronicInvoicing` + `CaeResult` |
| `app/domain/invoice/credentials.py` (+ resolver port) | CREATE — `TaxCredential` (CUIT/cert/key cifrados), repo port |
| `app/application/invoice/use_cases.py` | CREATE — `IssueInvoice` (calcula neto/IVA, deriva tipo, pide CAE, persiste), `ListInvoices`, `GetInvoice` |
| `app/application/invoice/connect_afip.py` | CREATE — alta/edición de credenciales fiscales del tenant (cert/key/ptoVta/condición) |
| `app/infrastructure/invoicing/{afip_wsaa,afip_wsfe,afip_invoicing,fake_invoicing}.py` | CREATE — WSAA (TA+CMS), WSFEv1 (zeep), adapter, fake |
| `app/infrastructure/invoicing/credentials_resolver.py` | CREATE — descifra cert/key del tenant |
| `app/infrastructure/persistence/{models,mappers,invoice_repo,tax_credentials_repo}.py` | UPDATE/CREATE — `InvoiceORM` + `TaxCredentialORM` (cifrados) + mappers + repos |
| `alembic/versions/0005_invoices.py` | CREATE — `invoices` + `tax_credentials` + RLS |
| `app/presentation/schemas/invoices.py`, `api/v1/invoices.py` | CREATE — emitir/listar comprobantes + conectar AFIP |
| `app/presentation/errors.py`, `config.py`, `container.py`, `main.py`, `.env.example` | UPDATE — errores, `INVOICING_PROVIDER` (afip\|fake), `AFIP_ENV` (homo\|prod), wiring |
| `tests/unit/test_invoice.py`, `tests/integration/test_e2e_invoices.py` | CREATE — cálculo IVA/tipo + e2e con `FakeInvoicing` (cobro→facturar→CAE) + RLS |
| `pyproject.toml` | UPDATE — `zeep` (SOAP) si se implementa directo |

### Frontend
| File | Acción |
|---|---|
| `src/api/types-operations.ts`, `invoices-api.ts` | UPDATE/CREATE — `InvoiceDTO` + cliente emitir/listar |
| `src/hooks/use-invoices.ts` | CREATE — `useOrderInvoice`, `useIssueInvoice`, `useInvoices` |
| `src/features/orders/order-page.tsx` | UPDATE — bloque "Facturar" en la comanda pagada (tipo + receptor → CAE) + ver comprobante |
| `src/features/invoices/invoices-page.tsx` | CREATE — listado de comprobantes (data table) |
| `src/features/integrations/` (o settings) | UPDATE — "Conectar AFIP" (cert/key/ptoVta/condición), estado |
| `src/components/shell/nav-config.ts`, `router.tsx` | UPDATE — sección "Facturación" |

## NOT Building
- **Factura E (exportación), FCE/MiPyME, comprobantes de crédito, percepciones/retenciones** — fuera del MVP.
- **Otros WS de AFIP** (padrón A13, constancia de inscripción, WSCT) — futuro.
- **Multi-moneda en comprobantes** — ARS primero.
- **PDF/representación impresa del comprobante** y envío por email — follow-up (primero el CAE; el PDF/QR AFIP después).
- **Libro IVA / exportación al contador** — es de la capa de inteligencia (fase posterior), se alimenta de estos `Invoice`.

---

## Step-by-Step Tasks (tramos)
> Orden: dominio → credenciales fiscales → persistencia/migración → **FakeInvoicing + use cases + API + tests** (todo el flujo sin AFIP) → **WSAA+WSFEv1 reales** (homologación) → frontend. Validar `ruff/mypy/pytest` y `tsc/lint/test/build` por tramo.

### T1 — Dominio `Invoice` + cálculo IVA/tipo
- `Invoice` + VOs (`InvoiceType/Status/DocType/Concept/VatItem`), errores, `InvoiceRepository`, port `ElectronicInvoicing` + `CaeResult`. Lógica pura de **cálculo neto/IVA** desde el total (minor units, redondeo AFIP) y **derivación de tipo** (condición emisor/receptor). **MIRROR:** `Payment`/`PaymentGateway`. **VALIDATE:** `pytest tests/unit/test_invoice.py` (IVA 21%, total = neto+iva; tipo A/B/C).

### T2 — Credenciales fiscales por tenant
- `TaxCredential` (CUIT/cert/key cifrados, ptoVta, condición, live_mode) + repo + resolver (descifra). **MIRROR:** Fase 3.5 (`PaymentCredential`/resolver/`FernetTokenCipher`). **VALIDATE:** `mypy` + test de resolver.

### T3 — Persistencia + migración 0005 (RLS)
- `InvoiceORM` + `TaxCredentialORM` + mappers + repos; migración `0005_invoices` (tablas + RLS `tenant_isolation` + GRANT). **MIRROR:** `0004_payment_credentials.py`. **VALIDATE:** `alembic upgrade/downgrade/upgrade`.

### T4 — `FakeInvoicing` + use cases + API + tests (sin AFIP)
- `FakeInvoicing` (CAE fijo + número incremental); `IssueInvoice` (cobro PAID → calcula → `authorize` → persiste con CAE o REJECTED); `ListInvoices`/`GetInvoice`. API `POST /orders/{id}/invoice`, `GET /invoices`. Container Selector `invoicing_provider`. e2e: onboard→comanda→cobro→**facturar**→CAE; RLS. **VALIDATE:** `ruff+mypy+pytest`.

### T5 — Adapter AFIP real (WSAA + WSFEv1) — homologación
- `AfipWsaa` (Login Ticket Request + firma CMS + cache de TA por tenant), `AfipWsfe` (`zeep`: `FECompUltimoAutorizado` + `FECAESolicitar`, auth header), `AfipInvoicing` (orquesta, resuelve credenciales del tenant, mapea tipos/códigos/errores). Config `INVOICING_PROVIDER=afip`, `AFIP_ENV=homo`. **GOTCHA:** TA cacheado (rate-limit), numeración sin huecos, `ImpTotal=ImpNeto+ImpIVA+...`, fechas `yyyymmdd`, cert/key **solo cifrados/env**. **VALIDATE:** prueba en **homologación** con CUIT de testing (manual).

### T6 — Frontend (facturar + comprobantes + conectar AFIP)
- Bloque **Facturar** en la comanda pagada (tipo + receptor DocTipo/DocNro → CAE, mostrar CAE/nro/vto); página **Comprobantes** (data table); **Conectar AFIP** (cert/key/ptoVta/condición) en Integraciones/Settings; nav "Facturación". **MIRROR:** Fase 3.5 frontend (integraciones) + data tables. **VALIDATE:** `tsc/lint/test/build`.

---

## Validation Gates
- **Backend:** `ruff` · `mypy` · `pytest` (cálculo IVA/tipo; e2e cobro→facturar→CAE con `FakeInvoicing`; RLS de invoices y tax_credentials; mapeo de rechazo) · `alembic 0005 round-trip`.
- **AFIP real:** prueba en **homologación** (TA emitido, `FECompUltimoAutorizado` ok, `FECAESolicitar` → CAE en un comprobante B de prueba).
- **Frontend:** `tsc + eslint + test + build`.
- **Manual:** un tenant con CUIT de homologación factura una comanda y obtiene CAE; otro tenant aislado (RLS).

## Risks / Open
- **Certificados/firma CMS:** la parte más delicada (X.509 + PKCS#7). Mitigar con un test de firma + el entorno de homologación; evaluar `pyafipws` detrás del port si la firma directa se complica.
- **Numeración correlativa sin huecos:** un CAE pedido y no persistido deja un hueco → usar `FECompUltimoAutorizado` justo antes y manejar idempotencia/errores con cuidado.
- **Redondeo de IVA:** `ImpTotal = ImpNeto + ImpIVA` debe cerrar exacto (AFIP valida) — testear casos límite.
- **Condición fiscal / tipo de comprobante:** reglas A/B/C según emisor+receptor; arrancar con B (consumidor final) que es el caso más común en gastronomía.
- **Rate-limit WSAA:** cachear el TA sí o sí (no pedir uno por request).
- **Prereqs del usuario:** sin CUIT + certificado + punto de venta habilitado, solo se puede avanzar con `FakeInvoicing` (T1–T4); T5 necesita esos datos en homologación.
- **Build vs Buy:** se mantiene Build detrás del port; si la integración directa se vuelve cara, se envuelve una lib o un proveedor (Buy) **sin tocar el dominio**.
