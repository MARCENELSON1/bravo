# Plan: Finanzas v2 — layout diseñado sobre el motor existente

## Summary
Rearmar la Pantalla Finanzas al layout de los mockups (`.claude/PRPs/research/wellnod-6-pantallas-cobertura.md` §2) **sin reescribir el motor** (Tandas A–F). Agrega: hero de ganancia neta, 6 áreas con acción, "los 3 gastos que más cambiaron", donut de distribución de gastos, sparklines y últimos movimientos. El backend nuevo es chico: 2 read models sobre `payments` (egresos por categoría con variación; movimientos recientes).

## User Story
Como dueño, quiero abrir Finanzas y ver de un vistazo mi ganancia del período, qué áreas están sanas o para actuar, en qué se me fue la guita y qué cambió — en lenguaje simple y con acciones, no KPIs crudos.

## Problem → Solution
Hoy Finanzas muestra los 7 KPIs en una grilla plana + diagnósticos + margen por producto. → Reencuadrar en la jerarquía de niveles del mockup, sumando variación de gastos, donut, sparklines y últimos movimientos.

## Metadata
- **Complexity**: Medium-Large (~16 archivos: ~7 backend, ~9 frontend)
- **Source**: research `wellnod-6-pantallas-cobertura.md` §2 + `proyecto Well Nod 2026/Pantalla Finanzas_` (mockups Finanzas_01–10)
- **Estimated Files**: ~16

## Contexto verificado del codebase
| Hecho | Detalle |
|---|---|
| **NO hay tabla Expense** | Los egresos son `PaymentORM` con `direction=OUTFLOW`, `status=CONFIRMED`, columna `category: String(60) nullable`, `counterparty`, `description`, `amount:BigInteger`, `created_at`. Cobros = `direction=INFLOW`. |
| Motor Finanzas | `app/application/finance/{dtos,use_cases}.py` + `GetFinanceOverview` compone `GetAdvisorReport` + `GetProductPerformance` + settings + inventory. `FinanceOverview` DTO ya trae `kpis[]`, `diagnostics[]`, `product_margins[]`, `projection`, `summary`. |
| KPIs disponibles | `prime_cost, food_cost, labor_cost, waste, net_margin, gross_margin, break_even, revpash, inventory_turnover` (cada `FinanceKpi` con value/previous/delta/status/healthy_low/high). |
| Serie diaria | `GET /analytics/revenue/daily` (`useRevenueDaily`) → sparklines de facturación + derivar "mejores días". |
| Frontend actual | `frontend/src/features/finance/finance-page.tsx` (FinancePage + FinanceBody + ProductRow), usa `GlassCard`, `useFinanceOverview`, `FINANCE_RANGES`/`rangeWindow`, `formatMoney`. Container `mx-auto max-w-7xl px-6 py-8`. |
| Patrón read model | `analytics_repo.py`: `Sql<X>ReadModel(port)`, `__init__(session_factory)`, `async with self._session_factory() as session`, filtro `tenant_id ==`, rangos `>= since / <= until`, `group_by`. `mix()` agrupa por `method, direction` — **mirror para agrupar por `category`**. |
| Patrón endpoint | `finance.py` router: `require_roles(OWNER, MANAGER)`, `from/to` alias, DI `Depends(Provide[Container.x])`, mapeo DTO→schema. |
| Wiring | `container.py`: `providers.Factory` para read model + use case; auto-wiring cubre `app.presentation`. |
| Tests | unit puros de `_build_finance_kpis` en `tests/unit/test_finance_overview.py`; e2e en `tests/integration/test_e2e_finance.py` (helper `_sell_with_recipe`, `_auth`, `_onboard_verify_login`). Egresos: `POST /expenses {category, amount}`. |

---

## Patterns to Mirror

### READ_MODEL_GROUP_BY (backend) — SOURCE: analytics_repo.py `SqlAlchemyPaymentMixReadModel.mix`
```python
stmt = (select(PaymentORM.category, func.coalesce(func.sum(PaymentORM.amount), 0))
        .where(PaymentORM.tenant_id == tenant_id,
               PaymentORM.direction == PaymentDirection.OUTFLOW.value,
               PaymentORM.status == PaymentStatus.CONFIRMED.value)
        .group_by(PaymentORM.category))
if since is not None: stmt = stmt.where(PaymentORM.created_at >= since)
if until is not None: stmt = stmt.where(PaymentORM.created_at <= until)
```

### USE_CASE_LECTURA — SOURCE: application/analytics/use_cases.py `GetRevenueDaily`
```python
class GetExpenseBreakdown:
    def __init__(self, read_model, tenant_context): ...
    async def execute(self, *, tenant_id, since=None, until=None):
        self._tenant_context.set(tenant_id)
        return await self._read_model.breakdown(tenant_id, since=since, until=until)
```

### ENDPOINT — SOURCE: finance.py `get_overview` (require_roles + from/to + map)
### FRONTEND_HOOK — SOURCE: hooks/use-analytics.ts `useRevenueDaily` (useQuery + queryKey + services)
### CHART_HANDROLLED — SOURCE: dashboard-page.tsx `RevenueChart` (barras a mano con divs; sin lib de charts)

---

## Files to Change

### Backend (motor de datos nuevo — chico)
| File | Action | Qué |
|---|---|---|
| `app/application/finance/read_models.py` (o dtos) | UPDATE | ports `ExpenseBreakdownReadModel` + `RecentMovementsReadModel` + dataclasses `ExpenseCategoryRow{category, amount, previous, delta}`, `MovementRow{occurred_at, kind(IN/OUT), amount, method, category, description}` |
| `app/application/finance/use_cases.py` | UPDATE | `GetExpenseBreakdown` (actual + previous window, un solo call) + `GetRecentMovements` |
| `app/infrastructure/persistence/finance_repo.py` | UPDATE | `SqlAlchemyExpenseBreakdownReadModel` (group OUTFLOW by category, actual + previo) + `SqlAlchemyRecentMovementsReadModel` (últimas N por created_at desc) |
| `app/presentation/schemas/finance.py` | UPDATE | `ExpenseBreakdownRowResponse`, `ExpenseBreakdownResponse`, `MovementResponse` |
| `app/presentation/api/v1/finance.py` | UPDATE | `GET /finance/expenses/breakdown` (from/to → categorías con amount+previous+delta) · `GET /finance/movements` (limit, últimas transacciones) |
| `app/container.py` | UPDATE | factories de los 2 read models + 2 use cases |
| `tests/integration/test_e2e_finance.py` | UPDATE | e2e: registrar egresos en 2 categorías → breakdown suma y delta; movimientos recientes lista cobro+egreso |

### Frontend (el grueso — reorganización visual)
| File | Action | Qué |
|---|---|---|
| `frontend/src/api/types-operations.ts` | UPDATE | `ExpenseBreakdownRowDTO`, `ExpenseBreakdownDTO`, `MovementDTO` |
| `frontend/src/api/finance-api.ts` | UPDATE | `expenseBreakdown(query)`, `recentMovements(query)` |
| `frontend/src/hooks/use-finance.ts` | UPDATE | `useExpenseBreakdown`, `useRecentMovements` |
| `frontend/src/features/finance/finance-hero.tsx` | CREATE | Hero: ganancia neta grande + comparativo + proyección |
| `frontend/src/features/finance/finance-areas.tsx` | CREATE | 6 tarjetas por área (semáforo + headline + acción), derivadas de KPIs + mejores días + proveedores |
| `frontend/src/features/finance/expense-donut.tsx` | CREATE | Donut SVG hand-rolled de distribución de gastos (clickeable → filtro) |
| `frontend/src/features/finance/expense-changes.tsx` | CREATE | "Los 3 gastos que más cambiaron" (top 3 por |delta|) |
| `frontend/src/features/finance/recent-movements.tsx` | CREATE | Lista de últimos movimientos (solo modo Hoy/Semana) |
| `frontend/src/components/ui/sparkline.tsx` | CREATE | Sparkline SVG chico reutilizable (para KPIs money) |
| `frontend/src/features/finance/finance-page.tsx` | UPDATE | Rearmar en niveles: Hero → 6 áreas → 3 gastos + donut → KPIs (acordeón, ya existen) → últimos movimientos. Reusa diagnósticos + margen por producto ya presentes |
| tests front (`*.test.ts`) | UPDATE | tests de los 2 clientes API nuevos (patrón vi.fn HttpClient) |

## NOT Building
- ❌ Variance esperado-vs-real (TVA/MarketMan) — necesita food cost teórico vs facturas reales; es otra fase.
- ❌ Benchmarking vs otros restaurantes (el doc dice "no MVP").
- ❌ Sparklines para TODOS los KPIs — solo los que tienen serie diaria (facturación/ganancia). Los de ratio sin serie histórica se difieren.
- ❌ Búsqueda IA embebida en Finanzas (existe como Copilot aparte; integrarla es otra tanda).
- ❌ Nuevas migraciones — todo sale de `payments` existente.
- ❌ Cambiar el motor (KPIs, diagnostics, snapshots, proyección) — se reusa tal cual.

---

## Step-by-Step Tasks

### Task 1 — Backend: read model de egresos por categoría (actual + previo)
- **ACTION**: Port `ExpenseBreakdownReadModel.breakdown(tenant_id, *, since, until) -> list[ExpenseCategoryRow]`. Impl agrupa `PaymentORM` OUTFLOW+CONFIRMED por `category` en la ventana (`amount`), y en la ventana previa de igual duración (`previous`); `delta = amount - previous`. Categoría `None` → "Otros".
- **MIRROR**: READ_MODEL_GROUP_BY. Ventana previa = `[since - (until-since), since]` (mirror de cómo el Asesor arma el período previo).
- **VALIDATE**: e2e — 2 egresos en "Proveedores" + 1 en "Servicios" → 2 filas con amount correcto.

### Task 2 — Backend: read model de movimientos recientes
- **ACTION**: `RecentMovementsReadModel.recent(tenant_id, *, since, until, limit=20) -> list[MovementRow]`. Últimas `PaymentORM` (INFLOW+OUTFLOW, CONFIRMED) por `created_at desc`, mapeando `kind` (IN/OUT), `amount`, `method`, `category`, `description`, `occurred_at`.
- **VALIDATE**: e2e — un cobro + un egreso → lista ordenada desc con ambos.

### Task 3 — Backend: use cases + schemas + endpoints + wiring
- **ACTION**: `GetExpenseBreakdown`, `GetRecentMovements` (mirror `GetRevenueDaily`). Schemas + `GET /finance/expenses/breakdown` y `GET /finance/movements` (require_roles OWNER/MANAGER, from/to). Wire en `container.py`.
- **VALIDATE**: `cd backend && pytest` verde; endpoints responden 200 con auth, 401/403 sin rol.

### Task 4 — Frontend: clientes API + hooks + tipos
- **ACTION**: DTOs + `finance-api.ts` (`expenseBreakdown`, `recentMovements`) + `use-finance.ts` hooks. Tests de cliente (patrón vi.fn HttpClient).
- **VALIDATE**: `npm run test` + `npm run build`.

### Task 5 — Frontend: componentes nuevos
- **ACTION**: `sparkline.tsx` (SVG mini), `finance-hero.tsx`, `finance-areas.tsx` (6 áreas: Tu dinero=net_margin, Costo comida=food_cost, Costo personal=labor_cost, Mermas=waste, Mejores días=derivar de revenue/daily, Proveedores=mayor delta del breakdown; headline por template + acción por status), `expense-donut.tsx` (SVG conic o arcos; ≤5 segmentos + "Otros"), `expense-changes.tsx` (top 3 por |delta| con explicación), `recent-movements.tsx`.
- **MIRROR**: CHART_HANDROLLED (barras a mano del dashboard); GlassCard para las tarjetas.
- **GOTCHA**: No hay lib de charts — donut y sparkline se dibujan a mano (SVG). Donut clickeable filtra la pantalla por categoría (estado local). Mantener el estilo Wellnod (glass, verde, tokens).
- **VALIDATE**: `npm run build` + revisión visual en claro/oscuro.

### Task 6 — Frontend: rearmar finance-page en niveles
- **ACTION**: Reordenar `FinanceBody`: (Hero) → (6 áreas) → (3 gastos + donut lado a lado) → (KPIs del rubro en acordeón — reusar la grilla actual) → (diagnósticos + margen por producto ya existentes) → (últimos movimientos, solo si range ∈ {today, week}). Selector temporal arriba (ya existe).
- **VALIDATE**: `npm run build` + `npm run test` + `npm run lint`; manual con datos reales (dev DB / prod) en claro y oscuro.

### Task 7 — Validación integral + merge
- **ACTION**: `cd backend && pytest` + `cd frontend && npm run build && npm run test && npm run lint`. Manual. Commit + merge `--no-ff` a `main` + push.

---

## Testing Strategy
| Test | Input | Expected |
|---|---|---|
| ExpenseBreakdown suma por categoría | 2 egresos Proveedores + 1 Servicios | 2 filas, amounts correctos, delta vs previo |
| ExpenseBreakdown ventana previa vacía | solo egresos este período | previous=0, delta=amount |
| RecentMovements orden | cobro + egreso | lista desc por created_at, kinds IN/OUT |
| Cliente API breakdown/movements | {from,to} | GET con auth:true, path correcto |
| RLS | 2 tenants | cada uno ve solo lo suyo (e2e) |
- Edge: sin egresos → breakdown [] (donut vacío, "sin gastos"); sin movimientos → lista vacía; categoría null → "Otros"; división por cero en shares del donut.

## Validation Commands
```bash
cd backend && pytest
cd frontend && npm run lint && npm run test && npm run build
```
EXPECT: todo verde. Manual: Finanzas en claro/oscuro, donut clickeable, últimos movimientos solo en Hoy/Semana.

## Acceptance Criteria
- [ ] Hero de ganancia neta + comparativo + proyección.
- [ ] 6 áreas con semáforo + headline + acción.
- [ ] "3 gastos que más cambiaron" con delta $ y explicación.
- [ ] Donut de distribución de gastos clickeable.
- [ ] Sparklines en los KPIs con serie.
- [ ] Últimos movimientos en modo Hoy/Semana.
- [ ] Motor intacto; suites back y front verdes; build verde.

## Risks
| Risk | Prob | Impacto | Mitigación |
|---|---|---|---|
| Donut/sparkline a mano queda tosco | Media | Bajo | SVG simple; iterar visual; consistente con las barras del dashboard |
| "Mejores días" necesita serie por día de semana | Media | Bajo | Derivar de `revenue/daily` agrupando por weekday en el front; si no alcanza, diferir esa área |
| 6 áreas: headline+acción se sienten inventados | Media | Medio | Templates deterministas por KPI+status (no LLM); honestos ("sano"/"revisar") |
| Categorías de egreso libres (texto) | Media | Bajo | Agrupar por `category` tal cual; null→"Otros"; top 5 + "Otros" en el donut |

## Notes
- Todo el backend nuevo sale de `payments` (OUTFLOW=egresos, INFLOW=cobros) — sin migraciones.
- Reusar el estilo Wellnod y `GlassCard`; el container ya es `max-w-7xl`.
- Después de esta fase, el doc de cobertura sugiere Home v2 (segundo mejor ROI).
