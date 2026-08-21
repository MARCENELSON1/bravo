# Plan: Cimiento de Comisiones — "la ganancia REAL después de comisiones"

## Summary
Hoy el pago guarda solo `amount` (bruto); Home/Finanzas/Mesas muestran bruto. La
comisión (MercadoPago/tarjeta se quedan un %) se **congela** en cada `Payment`
(`fee_amount` + `net_amount`, mismo patrón que 2B congeló netos en `sale_facts`),
con tasa **0 por default → net == bruto == hoy (paridad total)**. Migración **0031**.
Se sirve el neto en Home hero y Finanzas; "Cobros por canal" queda bruto con nota.

## La distinción crítica (NO pisar 2B)
- **2B (IVA)** vive en `sale_facts` (`line_net_amount`/`food_cost_net_amount`) → eje
  **margen** (venta neta de impuesto − costo neto), por línea de venta.
- **Comisión** vive en el **`Payment`** (`net_amount = amount − fee`) → eje **cobro
  financiero** (lo que entra a la cuenta tras la retención del gateway), por cobro.
- **Ortogonales:** la comisión NO se resta del margen por-producto (evita doble conteo).
  `sale_facts`/snapshot **no cambian**. Un cobro de $1000 con IVA 21% tiene venta neta
  ~$826 (margen) Y neto financiero $970 (comisión 3%) — dos números, dos ejes.

## Decisiones (recomendación del plan)
1. **Fuente de la comisión:** MVP = **tasa configurable por método por tenant** (bps).
   Slice C: para MERCADOPAGO/QR (online, webhook) sobre-escribir con la **comisión
   real** de MP; tarjeta manual/efectivo = tasa estimada. Empezar por la tasa (100% paridad).
2. **Dónde se guarda:** tabla nueva **`payment_fee_rates(tenant_id, method, fee_bps)`**
   (PK `(tenant_id, method)`, RLS, sin filas → 0 bps → paridad). NO `advisor_settings`
   (es por-método + `UpdateAdvisorSettings` reconstruye la entidad → lost-update).
3. **Qué se persiste:** congelar `fee_amount` + `net_amount` en el pago (estable ante
   cambios de tasa). Nullable + `COALESCE(net_amount, amount)` para históricos.
4. **Bruto vs neto:** Home hero + Finanzas → **neto financiero** (`sum(net_amount)`) +
   línea "Comisiones $X"; "Cobros por canal" → **bruto con nota**; Mesas → bruto (no se
   toca); margen del Asesor → **no** se le resta comisión (ortogonal a 2B).

## Slice A — Cimiento invisible (paridad total, 0 cambios visibles)
Infra completa con tasas 0 → `net==amount` en todos lados.
- **Migración 0031:** `payments.fee_amount` + `payments.net_amount` (BigInteger nullable);
  tabla `payment_fee_rates` (+ RLS). Opcional `UPDATE payments SET net_amount=amount`.
- `domain/payment/entities.py`: `fee_amount: int = 0`, `net_amount: int | None = None`.
- Helper `fee_of(amount, bps) = round(amount*bps/10000)` (int, patrón `split_vat`, sin float).
- Puerto `PaymentFeeRateRepository.rates_for(tenant_id) -> dict[method, bps]` + adapter.
- `RegisterPayment.execute`: resolver `fee_bps` del método (default 0), estampar
  `fee_amount`+`net_amount` antes de `add`. Inyección **opcional** (None→0→paridad, patrón `cash`/`policy`).
- ORM `PaymentORM` (+2 cols) + `PaymentFeeRateORM`; mappers; `payment_columns.py` (espejo de
  `sale_fact_columns.py`): `net_collected_col()=coalesce(net_amount, amount, 0)`; container wiring.
- **Front:** ninguno. **Migración:** SÍ. **Riesgo/Tamaño:** M (path caliente de cobro).
- **Tests:** `fee_of` (0→0, 300bps/1000→30, redondeo); `RegisterPayment` net==amount sin tasas
  (paridad) y net<amount con tasa; mapper round-trip; RLS de la tabla nueva.

## Slice B — Mostrar el neto REAL (config + read models + UI)
El diferencial visible.
- `GetPaymentFeeRates` + `UpdatePaymentFeeRates` (upsert por método, sin lost-update);
  GET/PUT `/payments/fee-rates`.
- `dashboard_repo.summary`: `collected_net = sum(net_collected_col())` + `fees_total`; hero → neto.
- finance (`finance_repo`/`finance_snapshot_repo`): `FinanceSummary +collected_net_amount +fees_amount`
  (sobre payments; `sale_facts` NO cambia). analytics `mix`: opcional net por canal.
- **Front:** tipos + hooks (`use-finance`/`use-dashboard`/`use-analytics`); hero neto + sub-línea
  "después de comisiones"; Finanzas línea "Comisiones"; "Cobros por canal" bruto con nota; form de
  tasas por método (patrón del campo "IVA %" de 2B); helper puro TS + `.test.ts`.
- **Migración:** NO. **Riesgo/Tamaño:** M-L (varias pantallas). **Paridad:** tasas 0 → neto==bruto.
- **Tests:** read-model con/sin tasas; upsert por método sin pisar otros; e2e cargar 3% MP → hero baja.

## Slice C — Comisión real del gateway (MP webhook, autoritativa online)
- `GatewayChargeStatus +fee_amount +net_amount`; `mercadopago_gateway.fetch_status` extrae de
  `/v1/payments/{id}` (`fee_details[].amount` / `net_received_amount`).
- `ConfirmGatewayPayment`: al confirmar, si trae fee real → sobre-escribe la estimada (online
  autoritativo); manuales conservan la estimada. Fallback sin fee → estimada (sin regresión).
- **Migración:** NO. **Riesgo/Tamaño:** S-M (forma de API externa; aislado en el gateway).

## NOT Building
Comisión por tramo/volumen; retenciones impositivas MP (IIBB/ganancias); fees de cash-out/transfer;
restar comisión al margen del Asesor (ortogonal a 2B); neteo de Mesas; backfill de comisiones reales
viejas (COALESCE a bruto).

## Riesgos
- **Doble conteo comisión vs 2B:** comisión SOLO en `Payment`; `sale_facts`/margen intactos + test de ortogonalidad.
- **Lost-update de tasas:** tabla dedicada + upsert por método.
- **Path caliente (A):** inyección opcional (None→0→paridad); tests de paridad primero.
- **API MP (C):** aislado en el gateway, fallback a estimado.
- **Redondeo bps:** helper único `fee_of` (int, patrón `split_vat`).

## Orden
A (cimiento, migración) → B (visible + config) → C (comisión real MP). Cada slice su rama + merge.

## Critical Files
- backend/app/application/payment/use_cases.py (RegisterPayment / ConfirmGatewayPayment)
- backend/app/infrastructure/persistence/models.py (PaymentORM + PaymentFeeRateORM)
- backend/app/infrastructure/persistence/mappers.py
- backend/app/infrastructure/persistence/dashboard_repo.py + finance repos
- backend/app/infrastructure/persistence/sale_fact_columns.py (patrón para payment_columns.py)
