# Implementation Report: Fase 4 — Facturación electrónica AFIP

## Summary
Facturación electrónica end-to-end detrás del port `ElectronicInvoicing`: de una
comanda **pagada** se deriva el tipo de comprobante (A/B/C según condición fiscal
del emisor + documento del receptor), se calcula neto/IVA, se pide el **CAE** y se
persiste el comprobante (multi-tenant + RLS). Dos transportes intercambiables vía
`Selector`: `FakeInvoicing` (dev/MVP, autoriza al instante) y `AfipInvoicing`
(WSAA + WSFEv1 reales). Credenciales AFIP (cert/key PEM) por tenant, cifradas con
Fernet y resueltas sólo en memoria. Frontend: bloque "Facturar" en la comanda,
pantalla Comprobantes y "Conectar AFIP" en Integraciones.

## Tasks Completed

| # | Tramo | Status | Notes |
|---|---|---|---|
| T1 | Dominio facturación + IVA | ✅ | VOs, entidades, `taxation` puro (split_vat/no_vat/invoice_type_for) |
| T2 | Credenciales fiscales por tenant | ✅ | `TaxCredential` + repo + resolver cifrado (reusa `TokenCipher`) |
| T3 | Migración 0005 (invoices + tax_credentials) | ✅ | RLS ENABLE/FORCE + policy tenant_isolation |
| T4 | FakeInvoicing + casos de uso + API + tests | ✅ | IssueInvoice idempotente, endpoints, 3 e2e |
| T5 | Adapter AFIP real (WSAA + WSFEv1) | ✅ | CMS/PKCS#7, cache TA, zeep en to_thread; mapeo testeado |
| T6 | Frontend facturación | ✅ | Facturar en comanda, Comprobantes, Conectar AFIP |

## Validation Results

| Level | Status | Notes |
|---|---|---|
| Static (ruff + mypy) | ✅ Pass | mypy 157 archivos sin issues; ruff app+tests limpio |
| Backend tests | ✅ Pass | suite completa 108 verdes (incl. 4 e2e facturación) |
| Frontend (tsc+eslint) | ✅ Pass | 0 errores |
| Frontend tests | ✅ Pass | 20 verdes (vitest) |
| Build | ✅ Pass | `vite build` OK |

## Deviations from Plan
- **T5 partido en dos commits**: primero el mapeo puro WSFEv1 (testeable,
  `wsfe_mapping.py` + 3 unit tests), luego el adapter SOAP/CMS (`afip_wsaa.py` +
  `afip_invoicing.py`). La E/S contra AFIP **no es unit-testeable** sin
  certificado de homologación: se valida en homologación AFIP.
- **Fix no planificado en IssueInvoice**: al reintentar un comprobante
  DRAFT/REJECTED se **reusa la fila** (id existente + `save`) en vez de crear
  otra; evita 2 filas por comanda y el `MultipleResultsFound` de
  `get_by_order` (que usa `scalar_one_or_none`). Cubierto por test e2e de
  reintento (rechazo → autoriza, una sola fila).

## Dependencies
- `zeep>=4.3,<5.0` (cliente SOAP, sync → `asyncio.to_thread`). `cryptography`
  (ya presente) firma el CMS del Login Ticket Request.

## Pendiente (fuera de código)
- **Validación en vivo**: requiere CUIT de homologación + certificado + alta de
  WSFE + punto de venta. La ruta SOAP es correcta-por-construcción.
- Considerar cache del TA en DB (hoy in-process; un restart puede chocar con
  "TA ya válido" hasta el vencimiento ~12 h).

## Next Steps
- [ ] Validar `AfipInvoicing` en homologación AFIP con certificado real.
- [ ] PR/merge `feat/fase-4-afip` → `main`.
