# Plan: Fase 8 — Modelo canónico + read models (CQRS-lite, medallion-lite en Postgres)

## Summary
El **puente captura → inteligencia**. Sobre la captura nativa (Fases 2–7) montamos una **capa analítica** que
normaliza los hechos del negocio a un **modelo canónico** (ventas, pagos/medios, gastos, productos) y expone
**read models de KPIs en pesos** (ingresos, ventas, egresos, **margen bruto**, ticket promedio, mix de medios de
pago). Es la base estable y segura que después consumen el asesor financiero, el dashboard y el copiloto (Capa 2).
Prioridad PRD: *Should* (puente). *Success* (PRD): los KPIs base se leen del **modelo canónico** para un tenant,
alimentados por la captura nativa.

> **DECISIONES DE ARQUITECTURA (cerradas — no re-litigar):**
> 1. **Medallion-lite DENTRO del mismo Postgres multi-tenant.** Nada de lake/warehouse/Spark/orquestador en el MVP
>    (lo confirma el PRD: *CQRS-lite, no warehouse, hasta escala*). Las capas son semánticas, no infra:
>    - **Bronze** = las **tablas operativas actuales** (system of record, dato first-party ya limpio). **No se
>      copian.** El bronze "raw real" recién aparece si se ingestan fuentes externas (MP/POS/foto-OCR) — diferido.
>    - **Silver** = **fact tables canónicas** tenant-scoped con **RLS** (forma única del hecho).
>    - **Gold** = **read models de KPIs detrás de ports** (Clean Arch), que leen el asesor/dashboard/copiloto.
> 2. **Silver se mantiene por proyección transaccional (push), reusando el patrón de Fase 6.** El hook de "comanda
>    → PAID" (`_settle_order`) que hoy dispara el `InventoryConsumer` se **generaliza** para también proyectar
>    `sale_facts`. **Idempotente** por `order_id` (guard tipo `exists_for_order`). Más un caso de uso de
>    **rebuild/backfill** para las comandas PAID que ya existen.
> 3. **Gold arranca *pull*, se promueve a tabla sólo lo caro.** `payment_facts` y los mixes salen *pull* (read model
>    que consulta `payments`, ya canónico-ish: direction/method/amount/category). Sólo `sale_facts` es **projection
>    table** (push) porque snapshotea food cost point-in-time y denormaliza categoría — el join caro que no querés
>    repetir.
> 4. **RLS también en la capa analítica** (son datos de plata). **GOTCHA Postgres:** RLS **no** aplica a
>    *materialized views* → las proyecciones son **tablas reales con RLS** (como migraciones 0006–0009), no matviews.
>    Si en el futuro se usa una matview para un agregado caro, se compensa con el filtro explícito por `tenant_id`
>    (defensa en profundidad que ya está en todos los repos).
> 5. **Read models detrás de ports.** El asesor depende del **port**, nunca del SQL — misma disciplina que
>    `StaffReportReadModel`/`FoodCostReadModel`. Vocabulario canónico = DTOs de lectura + ports en `application/analytics/`.
> 6. **Money entero + moneda del tenant**; timestamps de servidor; multi-tenant + RLS en todo.

## Estado de implementación
PENDIENTE. Depende **sólo de Fases 2 (comandas) + 3 (pagos)** — ✅ en `main`. Aprovecha además 6 (food cost) y 7
(no-shows) que ya están. Se implementa en rama `feat/fase-8-modelo-canonico`. Migración nueva: **0010_sale_facts**.

## User Story
Como **dueño/encargado** quiero **ver en pesos cómo me fue** (ingresos, gastos, margen, ticket, en qué cobré) leído
de **una sola fuente consistente**, para **decidir sin cruzar planillas** — y que esa fuente alimente después al asesor.

## Problem → Solution
Hoy cada pantalla calcula sus números con su propio SQL (`dashboard_repo`, `staff_report_repo`, `food_cost_repo`):
read models sueltos, sin una verdad única. → **Modelo canónico** (silver) + **read models de KPIs** (gold) detrás de
ports: una "venta" tiene una sola forma, los KPIs base se derivan de ahí, y queda el contrato estable que consumen
asesor/dashboard/copiloto. Todo scoped por `tenant_id` + RLS.

---

## Modelo canónico (silver) — fact tables
- **`sale_facts`** (projection table, push, RLS). Grano = **línea de comanda PAID** (un row por `order_item`):
  `id, tenant_id, order_id, order_item_id, product_id, product_name (snapshot), category (snapshot|None),
  quantity, unit_price_amount, line_amount (qty×precio), food_cost_amount|None (snapshot del food cost de la receta
  al momento de la venta; None si el producto no tiene receta), currency, waiter_id, table_id|None,
  occurred_at (= paid_at), created_at`. Habilita ventas (accrual), ticket (agg por order), product performance y
  **margen bruto** (line_amount − food_cost).
- **`payments`** (ya existe) = fuente canónica de **pagos** (cobros INFLOW + egresos OUTFLOW, con method/category).
  No se crea tabla nueva: el read model lo consulta directo (*pull*).
- *(Secundario / Fase 7)* **no-shows / covers**: se derivan *pull* desde `reservations` (status NO_SHOW, party_size
  por turno). Va como read model de gold opcional (T4 o diferido).

## Proyección (el "ETL")
- **Port `SalesProjector`** (`application/analytics/ports.py`): `project_order(tenant_id, order_id)`.
- **`ProjectOrderSales`** (`application/analytics/projection.py`) implementa el port: dado un `order_id` PAID, si
  **no** hay ya `sale_facts` para ese order (idempotencia), inserta un row por `order_item` con snapshot de
  nombre/categoría/precio + **food cost al momento** (best-effort vía el read model/repos de inventory; None si no
  hay receta) y `occurred_at = now`.
- **Enganche:** el settle de pagos (`_settle_order`) gana un **segundo colaborador opcional** (junto al
  `InventoryConsumer`). Recomendado: pasar una **lista de hooks post-PAID** (`list[OrderPaidHook]`) o un segundo
  param opcional `sales_projector`. En tests se overridea con fake/no-op. El pago depende de **ports**, no de analytics.
- **`RebuildSalesFacts`** (`application/analytics/rebuild.py`): backfill — proyecta todas las comandas PAID del
  tenant que aún no tengan facts (idempotente). Endpoint admin (OWNER) `POST /analytics/rebuild`.

## Read models de KPIs (gold) — detrás de ports
- **`RevenueReadModel`** → `RevenueSummary {sales_amount (Σ sale_facts.line_amount), collected_amount (Σ payments
  INFLOW CONFIRMED), expense_amount (Σ payments OUTFLOW), food_cost_amount (Σ sale_facts.food_cost), gross_margin
  (sales − food_cost), orders_count, average_ticket (sales/orders), currency}` para `[since, until]`.
- **`PaymentMixReadModel`** → lista `{method, direction, amount, count}` (pull sobre `payments`).
- **`ProductPerformanceReadModel`** → top productos `{product_id, name, units_sold, sales_amount, food_cost_amount,
  margin_amount}` (sobre `sale_facts`).
- *(Secundario)* **`NoShowReadModel`** → `{covers, no_shows, no_show_rate_bps}` por turno (pull sobre `reservations`).
- Use cases finos `GetRevenueSummary` / `GetPaymentMix` / `GetProductPerformance` (setean tenant_context).

## Config
- (Opcional) zona horaria del tenant para bucketear "día" en `occurred_at` — **diferido** (MVP: filtra por rango
  `from/to` en UTC, como `shifts`/`reservations`).

---

## Mandatory Reading (moldes ya en el repo)
- **Read models existentes (molde gold + a consolidar):** `application/reporting/dashboard.py` +
  `infrastructure/persistence/dashboard_repo.py`; `application/reporting/staff.py` + `staff_report_repo.py`;
  `application/inventory/food_cost.py` + `infrastructure/persistence/food_cost_repo.py`.
- **Proyección transaccional (molde push, reusar):** `application/payment/use_cases.py` (`_settle_order` +
  inyección opcional del colaborador), `application/inventory/{ports,consume}.py` (port + caso de uso idempotente
  por `order_id`), `container.py` (cableado del colaborador **antes** de pagos).
- **Persistencia + migración RLS:** `alembic/versions/0009_reservations.py`, `models.py`, `mappers.py`,
  `infrastructure/persistence/{reservation_repo,shift_repo}.py`, `tests/integration/conftest.py` (`_TABLES`).
- **API + RBAC + errores + router:** `presentation/api/v1/{reports,inventory}.py`, `rbac.py`, `errors.py`, `main.py`.
- **Money / agregación entera:** `domain/shared/money.py`, `domain/inventory/costing.py`.
- **Frontend:** `api/inventory-api.ts` + `hooks/use-inventory.ts` + `features/inventory/stock-page.tsx` (sección
  food cost = tabla de KPIs), `features/dashboard/dashboard-page.tsx`, `lib/money.ts`,
  `services/services-{context,provider}`, `test/test-utils.tsx`, `components/shell/nav-config.ts`, `app/router.tsx`.

## Files to Change (orientativo)
**Backend (nuevos):** `application/analytics/{__init__,ports,projection,rebuild,read_models,use_cases}.py`,
`infrastructure/persistence/{sale_facts_repo,revenue_repo,payment_mix_repo,product_performance_repo}.py`,
`presentation/api/v1/analytics.py`, `presentation/schemas/analytics.py`, `alembic/versions/0010_sale_facts.py`,
tests unit + e2e.
**Backend (editar):** `models.py`, `mappers.py`, `container.py`, `presentation/errors.py`, `main.py`,
`application/payment/use_cases.py` (segundo hook post-PAID), `tests/integration/conftest.py` (`_TABLES` ← prepend
`sale_facts`).
**Frontend (nuevos):** `api/{types-analytics,analytics-api}.ts` (+ test), `hooks/use-analytics.ts`,
`lib/analytics.ts` (+ test), `features/analytics/analytics-page.tsx`.
**Frontend (editar):** `services/services-{context,provider}`, `test/test-utils.tsx`, `nav-config.ts`
(grupo "Resumen" o "Finanzas" → "Analítica"), `app/router.tsx`.

---

## Step-by-Step Tasks

### T1 — Silver: `sale_facts` + proyección transaccional (push)
- ORM `sale_facts` + mapper + repo (`add_many`, `exists_for_order`, `list`/agregaciones). **Migración
  `0010_sale_facts`** (down `0009_reservations`): create + GRANT + ENABLE/FORCE RLS + policy `tenant_isolation`.
  `conftest._TABLES` ← prepend `sale_facts`.
- Port `SalesProjector` + `ProjectOrderSales` (idempotente por `order_id`, snapshot de food cost best-effort) +
  enganche en `_settle_order` (segundo colaborador opcional) + `RebuildSalesFacts` (backfill).
- **Tests:** proyección al pasar a PAID crea N facts (idempotente: re-settle no duplica); snapshot food cost
  presente sólo si hay receta; rebuild backfillea PAID previas; RLS.
- **MIRROR:** `application/inventory/{ports,consume}.py`, `_settle_order`, `0009_reservations.py`, `models.py`.

### T2 — Gold: read models de KPIs + API
- `RevenueReadModel`/`PaymentMixReadModel`/`ProductPerformanceReadModel` (ports) + adapters SQLAlchemy
  (revenue/product sobre `sale_facts`+`payments`; mix *pull* sobre `payments`). Use cases `GetRevenueSummary`/
  `GetPaymentMix`/`GetProductPerformance`. Router `/analytics/*` (OWNER/MANAGER, query `from/to`) + `POST
  /analytics/rebuild` (OWNER). Container + `errors.py` + `main.py`.
- **Tests e2e:** comanda PAID → revenue summary (ingresos/ventas/margen/ticket) correcto; mix de medios suma por
  método; product performance ordena por ventas; egresos = Σ OUTFLOW; RLS.
- **MIRROR:** `application/reporting/staff.py` + `staff_report_repo.py`, `presentation/api/v1/reports.py`.

### T3 — Frontend: página Analítica (KPIs en pesos)
- `AnalyticsApi` + `use-analytics` hooks; registrar en `services-{context,provider}` + `test-utils`. `lib/analytics.ts`
  (formato de KPIs/bps). Página **Analítica** (`/app/analytics`, OWNER/MANAGER): tarjetas de KPIs (ingresos, ventas,
  egresos, **margen**, ticket), tabla de **mix de medios**, tabla **top productos**; selector de período. Nav +
  ruta. (El dashboard existente puede quedar; consolidarlo para que lea del modelo canónico = follow-up.)
- **Validar:** tsc + eslint + vitest + build.
- **MIRROR:** `features/inventory/stock-page.tsx` (tablas de KPIs), `features/dashboard/dashboard-page.tsx`,
  `hooks/use-inventory.ts`, `api/inventory-api.ts`.

### T4 (secundario / opcional) — No-shows + covers (consume Fase 7)
- `NoShowReadModel` (pull sobre `reservations`) + `GET /analytics/no-shows` + tarjeta en Analítica. Si el alcance
  aprieta, **diferir** a Fase 9 (es dimensión del asesor, no KPI base del *Success*).

---

## Validation Commands
- **Backend:** `poetry run ruff check app tests` · `poetry run mypy app` · `poetry run pytest -q` (cobertura ≥ 80%
  en domain/application).
- **Frontend:** `npx tsc --noEmit` · `npx eslint src` · `npx vitest run` · `npx vite build`.

## Acceptance Criteria
- Una comanda que pasa a **PAID** proyecta `sale_facts` (un row por ítem, con snapshot de precio y food cost si hay
  receta); re-conciliar **no duplica**; `rebuild` backfillea las PAID previas.
- Los **KPIs base** (ingresos, ventas, egresos, **margen bruto**, ticket promedio, **mix de medios de pago**) se
  leen del **modelo canónico** para un tenant y dan correcto.
- Todo scoped por tenant (**RLS también en silver/gold**). ruff + mypy + pytest + tsc + eslint + vitest + build verdes.

## Complexity / Confidence
- **Complejidad:** Media. La proyección idempotente enganchada al settle ya tiene molde exacto (Fase 6 T4). Lo fino
  es el **diseño del vocabulario canónico** (no sobre-modelar) y el snapshot de food cost point-in-time. Las
  agregaciones de gold son SQL sobre patrones probados (`staff_report_repo`).
- **Confianza:** Alta en T1 (push reusa Fase 6) y T3. Media en T2 (definir el set mínimo de KPIs sin scope creep).

## Out of scope (diferido)
- Warehouse / lakehouse / medallion "de verdad" (Spark/Delta/object storage), dbt, orquestador (Airflow) — recién a
  escala / cross-tenant / multi-fuente. Bronze raw de **fuentes externas** (MP/POS/foto-OCR). Vistas materializadas
  (por el gotcha de RLS). Consolidar/retirar los read models ad-hoc actuales (`dashboard_repo` etc.) para que lean
  del canónico — follow-up incremental. KPIs avanzados del asesor (punto de equilibrio, labor/prime cost, mermas
  teórico-vs-real, RevPASH) e insights proactivos → **Fase 9**. CRM de clientes / `customer_dim` con identidad →
  Fase 12 (hoy `customer_name` sólo se snapshotea en reservas; sin entidad Cliente).
