# Plan: Paquete "4 guardas de confianza" (BRAVO/Wellnod)

## Summary
4 guardas, cada una el "titular" de un spec de dev auditado, bajo la filosofía **"nunca
mostrar un número inflado"**. Priorizan **paridad/seguridad** (default u off == hoy).
Empaquetado: **un PRP umbrella, 4 slices** — A+C sin migración (mismo PR posible), **B y D
en PRs propios con migración independiente** (rollback atómico).

## Hechos del repo (validados)
- Migraciones hasta `0027`; libres **0028**, **0029**.
- `DomainError` (`code` EN + `message` ES) → HTTP en `presentation/errors.py:~102` (`_STATUS_BY_TYPE`).
- Flags por tenant off-by-default viven en `AdvisorSettingsORM` (`models.py:671`, patrón `default_vat_bps=0`).
- `PaymentORM.created_at` existe (tz-aware); **NO** tiene `cash_session_id`.
- `/reports/staff` (`reports.py:45`) ya usa `Query(alias="from"/"to")` → template para el dashboard con fecha (C).
- Arqueo (`cashier/use_cases.py:_arqueo_inputs`) **ignora OUTFLOW** → mover propina a pasivo **no cambia el arqueo** (paridad gratis).

---

## A) Guarda de sanidad del food cost (spec Insumos) — S, sin migración, riesgo bajo
Banda de plausibilidad sobre el ratio ya calculado: fuera de **500–9500 bps (5%–95%)** →
"Receta incompleta / revisar". Flag **derivado** (calca `cost_confirmed` de Fase 3).
**Complementa Fase 3/6:** `cost_confirmed` mide "¿respaldado por compras?"; la banda mide
"¿el ratio es plausible?" (una receta 100% confirmada con 1 de 8 insumos cargados da food
cost 3% y `coverage_bps` no lo detecta).
- Dominio: `FOOD_COST_SANE_MIN_BPS=500`/`MAX_BPS=9500` en `value_objects.py`.
- Backend: `FoodCostRow +ratio_sane: bool=True` (seteado en `food_cost_repo.py:~255-266`);
  `FoodCostRowResponse` + `FoodCostRowDTO` exponen el bool.
- Front: `catalog-rows.ts` (`ratioSane`); badge en `product-catalog.tsx:~244`,
  `product-ficha.tsx:~142`, `stock-page.tsx`; en `menu-engineering-view.tsx:~36-42` las fuera
  de banda se excluyen de las conclusiones de plata (igual que hoy los `!cost_confirmed`).
- **A1** (mínimo): flag + exclusión de la plata, mantiene el número con warning.
- **A2** (opcional, forma fuerte): reemplaza margen/ratio por "—/revisar" fuera de banda.
- Paridad: recetas sanas → `ratio_sane=True` → cero cambio. Tests: row 300/9800 bps → False,
  3000 → True; `catalog-rows.test.ts` + test de exclusión en menu-engineering.

## B) `payments.cash_session_id` + bloquear cobro sin caja (spec Barra+Caja) — M/L, migr 0028, riesgo ALTO
Estampar la caja abierta en el cobro; rechazar sin caja detrás de flag por tenant OFF. Rollout 4 fases:
- **B1** (invisible): migr **0028** `payments.cash_session_id` UUID **nullable** + FK + index;
  `advisor_settings.require_open_cash_session BOOL NOT NULL server_default 'false'`.
  `Payment.cash_session_id: str|None=None`; mappers (`~396-420`); `RegisterPayment` inyecta
  `CashSessionRepository`, estampa `get_open(tenant).id` o `None` (paridad); rewire `container.py:677`.
  Estampar en `RegisterPayment` (no en el webhook; `ConfirmGatewayPayment` hereda).
- **B2** (backfill idempotente): asignar `cash_session_id` cruzando
  `payments.created_at ∈ [opened_at, coalesce(closed_at, now))` por tenant; sin caja → NULL.
- **B3** (enforcement): error `NoOpenCashSession` (`code=no_open_cash_session`, ES "Abrí la caja
  antes de cobrar.") → 409 en `errors.py`. Si flag ON **y** `get_open`=None → raise. Default OFF = hoy.
- **B4** (front): cobro maneja 409 con CTA "Abrí caja para cobrar" → `cash-session-page.tsx`.
- Paridad: nullable + flag OFF ⇒ B1/B2 invisibles. Tests: estampa con caja; sin caja+OFF cobra
  (paridad); sin caja+ON → `NoOpenCashSession`; migración upgrade/downgrade + backfill.

## C) Home: sacar margen inflado + regla de guarda + período único (spec Home, B1/B4) — S/M, sin migración, riesgo medio
Corrección real (no flag): `dashboard_repo.py:27-45` suma pagos **sin filtro de fecha** pero la
UI rotula "hoy", mientras "Cobros por canal" sí filtra → contradicción.
- Backend: `SqlAlchemyDashboardReadModel.summary` + `GetDashboardSummary` + `/reports/dashboard`
  aceptan `since/until` (patrón de `/reports/staff`), filtran `PaymentORM.created_at`.
- Front: `use-dashboard.ts` + `reports-api.ts` pasan `from=startOfTodayIso()` → hero alineado con Cobros por canal.
- Regla de guarda: si `expenses===0 && sales>0`, margen = ventas es inflado → renderizar
  **tentativo** ("faltan egresos / estimado", atenuado). (Opcional: `expenses_incomplete: bool` canónico.)
- **B4** dedupe: hero (`net`, `dashboard-page.tsx:~110-121`) y tarjeta "Tu margen hoy" (`~135-141`)
  muestran el mismo número → la tarjeta pasa a composición/cobertura, `net` solo en el hero.
- **NO** es paridad-cero por diseño (totales pasan de all-time a "hoy" = la corrección buscada).
  Tests: read-model con ventana; regla de guarda pura; ajustar tests viejos que asumían all-time.

## D) Propina como pasivo `tips_payable` (spec Barra+Caja) — M, migr 0029, riesgo medio
`PayTips` (`tips.py:71-99`) liquida vía `RegisterExpense` OUTFLOW cat "Propinas" → pega en el
resultado y muestra email/UUID. Cambiar a ledger neutro + mostrar `users.name`.
- Migr **0029**: tabla `tip_payouts` (id, tenant_id, waiter_id, amount, method, created_at) RLS;
  `TipPayoutORM` + entity/repo.
- `PayTips` escribe en el ledger (no `RegisterExpense`); rewire `container.py:733`. Ya no es
  OUTFLOW → nunca entra a Egresos/resultado.
- `TipsReadModel` (`tips_repo.py`): `paid` = **UNION** ledger nuevo + legacy OUTFLOW-Propinas
  (sin reescribir historia; los viejos ya impactaron meses cerrados).
- Nombre: `TipsReportRow.waiter_email` → `waiter_name` (`UserORM.name`, fallback email);
  `tips-page.tsx` muestra nombre.
- Arqueo: sin cambios (ya ignora OUTFLOW) → paridad total. Tests: `PayTips` escribe ledger y no
  crea OUTFLOW; report earned/paid/pending con mezcla legacy+ledger; front muestra `waiter_name`.

---

## Orden recomendado
1. **C** (bug real, sin migración, alinea el Home a período único).
2. **A** (flag derivado, calca Fase 3/6, sin migración).
3. **B** (la más riesgosa; rollout escalonado; PR propio, migr 0028).
4. **D** (ledger; PR propio, migr 0029).
A+C pueden ir juntas (display, cero migración). B y D en PRs propios por la migración + path de plata.

## Critical Files
- backend/app/application/payment/use_cases.py (B)
- backend/app/infrastructure/persistence/food_cost_repo.py (A)
- backend/app/infrastructure/persistence/dashboard_repo.py (C)
- backend/app/application/cashier/tips.py (D)
- backend/app/infrastructure/persistence/models.py (B: `PaymentORM.cash_session_id` + flag; D: `TipPayoutORM`)
- backend/app/container.py (rewire `register_payment`, `pay_tips`)
