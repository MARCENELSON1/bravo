# Plan: Pantalla Finanzas (el cerebro financiero del local)

## Summary
Una **Pantalla Finanzas unificada** (`/app/finanzas`) que reemplaza la fragmentación actual (analytics + advisor + caja) por una sola vista con los **7 KPIs gastronómicos vitales**, comparativos vs período previo, proyección de cierre, diagnósticos en lenguaje natural y drill-down — sobre una **arquitectura de datos de 3 capas** (live → snapshots pre-calculados → diagnostics LLM cacheados). Implementa exactamente lo prescripto en `Pantalla Finanzas .md`.

## User Story
Como **dueño/encargado de un restaurante**, quiero **una sola pantalla que me diga al instante cómo va la plata (los 7 números que importan), qué cambió vs antes y qué hacer al respecto**, para **tomar decisiones operativas sin esperar ni interpretar planillas**.

## Problem → Solution
**Hoy:** el "cerebro" analítico existe pero está partido en 3 pantallas (`/app/analytics`, `/app/advisor`, `/app/caja`), faltan 3 de los 7 KPIs (RevPASH, rotación de inventario, proyección de cierre), el Labor Cost sale de un número configurado a mano (no de horas reales), los diagnósticos LLM se regeneran en cada request (caro y lento), y no hay capa de snapshots → no escala.
**Objetivo:** una Pantalla Finanzas única, instantánea y accionable, fiel al doc, con los 3 layers de datos bien diseñados desde el arranque.

## Metadata
- **Complexity**: XL (dividido en 6 tandas independientes, mergeables una por una)
- **Source doc**: `Pantalla Finanzas .md` (raíz del repo) — benchmarking + KPIs vitales + arquitectura de 3 capas + lógica visual
- **Source PRD**: N/A (free-form desde el doc de diseño)
- **Estimated Files**: ~45 (backend + frontend + tests, repartidos por tanda)
- **Reglas del proyecto**: `CLAUDE.md` (Clean Architecture, dependencias hacia adentro, todo servicio externo tras un port, multi-tenant con filtro `tenant_id` + RLS, código en inglés / UX en español, tests 80%+ en dominio y casos de uso).

---

## Decisiones tomadas (del doc — NO re-preguntar)
> El usuario pidió implementar **exactamente** lo que detalla el documento. Estas decisiones salen del doc, no son abiertas (ver memoria `feedback-seguir-spec-doc`):
- **Pantalla unificada** (sección "Propuesta de lógica visual — Arquitectura de la pantalla"): una sola Pantalla Finanzas con selector temporal + los 7 KPIs.
- **Arquitectura de 3 capas** ("Arquitectura de datos sugerida"): live → **snapshots** → **diagnostics** cacheados. "Es importante diseñar bien esa parte desde el principio" → el contrato `FinanceOverviewReadModel` se diseña en Tanda A para que los snapshots (Tanda F) sean un swap de implementación detrás del mismo port.
- **Los 7 KPIs** ("KPIs gastronómicos vitales"): Prime Cost, Food Cost %, Labor Cost %, Margen de contribución por producto ($), RevPASH, Mermas %, Rotación de inventario. (NO incluir métricas de vanidad: ticket aislado, ROI mensual, cubiertos, growth-vs-año sin ajustar.)
- **Labor Cost** "sensible a horas extras y eficiencia de turnos" → de **horas reales del fichaje** × valor/hora (Tanda D), con fallback al costo mensual configurado.
- **Best practices** ("Mejores prácticas a adoptar"): comparativos siempre visibles, proyección de cierre mensual, diagnóstico de variaciones inusuales, drill-down ≤3 clics.
- **Selector temporal** ("Filtros temporales indispensables"): Hoy / Esta semana / Este mes (default) / Trimestre / Comparar períodos.

---

## UX Design

### Before
```
3 pantallas separadas, sin selector de rango unificado, sin los 7 KPIs juntos:
  /app/analytics → Ventas, Cobrado, Egresos, Margen bruto, Ticket, Food cost + tablas
  /app/advisor   → KPIs (food/labor/prime/net/break-even) + insights narrados
  /app/caja      → arqueo del turno  /app/propinas → propinas por mozo
```

### After
```
┌──────────────────────────────────────────────── /app/finanzas ──────────────┐
│  Finanzas                          [ Hoy · Semana · Mes* · Trimestre · ⇄ ]   │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌── Prime Cost ──┐ ┌── Food % ──┐ ┌── Labor % ──┐   (cada uno con Δ vs       │
│  │ 58%  ▼2pts ✓  │ │ 31% ▲1 ✓   │ │ 27% ▼1 ✓   │    período previo + rango   │
│  └────────────────┘ └────────────┘ └────────────┘    sano coloreado)         │
│  ┌── RevPASH ─────┐ ┌── Mermas % ┐ ┌── Rotación ─┐                            │
│  │ $X/asiento·h   │ │ 2.4% ✓     │ │ 3.1x       │                            │
│  └────────────────┘ └────────────┘ └────────────┘                            │
│  Proyección de cierre del mes: "Si seguís así, cerrás en $X" (run-rate)       │
├──────────────────────────────────────────────────────────────────────────────┤
│  Diagnósticos (lenguaje natural, cacheados):                                  │
│   • "De cada $100 que cobrás, $31 se van en ingredientes — sano."             │
│   • "⚠ Tu mermas subió 1.2pts vs el mes pasado — revisá la cocina."           │
├──────────────────────────────────────────────────────────────────────────────┤
│  Margen de contribución por producto ($)  →  drill-down ≤3 clics              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Interaction Changes
| Touchpoint | Before | After | Notes |
|---|---|---|---|
| Ver finanzas | 3 pantallas distintas | 1 pantalla `/app/finanzas` | analytics/advisor quedan accesibles pero la home financiera es esta |
| Rango temporal | `from/to` manual (date inputs) | Selector Hoy/Semana/Mes/Trim/Comparar | el front calcula el rango; el back ya acepta `since/until` |
| Comparar | no hay | Δ vs período previo en cada KPI | el advisor ya computa `previous` |
| Diagnóstico | se regenera por request | cacheado, instantáneo | Tanda C |
| Drill-down | tabla plana | general → producto → ítem (≤3 clics) | Tanda B |

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | `Pantalla Finanzas .md` | 1-146 | La spec: 3 capas, 7 KPIs, best practices, selector |
| P0 | `backend/app/application/advisor/report.py` | 23-135 | Motor de KPIs + comparación con período previo (núcleo a reusar) |
| P0 | `backend/app/domain/advisor/kpis.py` | 58-108 | `AdvisorKpis` + props prime_cost/net_margin/break_even |
| P0 | `backend/app/domain/advisor/insights.py` | 20-159 | `detect_insights` + códigos de insight |
| P0 | `backend/app/application/analytics/read_models.py` | 11-74 | Patrón port + DTO frozen + read model |
| P0 | `backend/app/infrastructure/persistence/analytics_repo.py` | 31-77 | Patrón query agregada con `since/until` |
| P1 | `backend/app/infrastructure/persistence/advisor_repo.py` | 27-104 | Metrics SQL + mermas valorizadas (qty×unit_cost/1000) |
| P1 | `backend/app/infrastructure/persistence/staff_report_repo.py` | 54-72 | Horas reales desde `ShiftORM` (para Labor real, Tanda D) |
| P1 | `backend/app/container.py` | 846-912 | Wiring de analytics + advisor (calcar) |
| P1 | `backend/alembic/versions/0011_advisor_settings.py` | 1-50 | Patrón de migración con RLS |
| P1 | `frontend/src/features/advisor/advisor-page.tsx` | 193-278 | Estructura de página KPIs + insights (a unificar) |
| P1 | `frontend/src/features/analytics/analytics-page.tsx` | 47-194 | KpiCard inline + tablas (a unificar) |
| P2 | `frontend/src/api/analytics-api.ts` + `hooks/use-analytics.ts` | all | Patrón API client + hook |
| P2 | `frontend/src/services/{services-context.ts,services-provider.tsx}` + `test/test-utils.tsx` | all | Registro de servicio en 3 archivos |
| P2 | `backend/tests/integration/test_e2e_advisor.py` | 13-74 | Patrón de test e2e con receta |

## External Documentation
No se necesita investigación externa — toda la lógica usa patrones internos ya establecidos (read models, advisor, RLS, React Query). El benchmarking del doc es contexto de producto, no dependencias técnicas.

---

## Patterns to Mirror

### READ_MODEL_PORT_DTO
```python
# SOURCE: backend/app/application/analytics/read_models.py:11-29
@dataclass(frozen=True)
class RevenueSummary:
    currency: str
    sales_amount: int        # accrual: Σ sale_facts.line_amount
    food_cost_amount: int    # Σ sale_facts.food_cost
    gross_margin_amount: int # sales − food_cost
    orders_count: int

class RevenueReadModel(ABC):
    @abstractmethod
    async def summary(self, tenant_id: str, *, since: datetime | None = None,
                      until: datetime | None = None) -> RevenueSummary: ...
```

### USE_CASE_DELEGATES_READ_MODEL
```python
# SOURCE: backend/app/application/analytics/use_cases.py:18-33
class GetRevenueSummary:
    def __init__(self, read_model: RevenueReadModel, tenant_context: TenantContext) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context
    async def execute(self, *, tenant_id: str, since=None, until=None) -> RevenueSummary:
        self._tenant_context.set(tenant_id)  # SIEMPRE setear el tenant antes de leer (RLS)
        return await self._read_model.summary(tenant_id, since=since, until=until)
```

### SQL_AGGREGATION_WITH_WINDOW
```python
# SOURCE: backend/app/infrastructure/persistence/analytics_repo.py:31-77
async with self._session_factory() as session:
    stmt = select(
        func.coalesce(func.sum(SaleFactORM.line_amount), 0),
        func.coalesce(func.sum(SaleFactORM.food_cost_amount), 0),
        func.count(func.distinct(SaleFactORM.order_id)),
    ).where(SaleFactORM.tenant_id == tenant_id)
    if since is not None: stmt = stmt.where(SaleFactORM.occurred_at >= since)
    if until is not None: stmt = stmt.where(SaleFactORM.occurred_at <= until)
```

### ADVISOR_PREVIOUS_PERIOD_COMPARISON
```python
# SOURCE: backend/app/application/advisor/report.py:84-94
kpis = self._build_kpis(metrics, settings, period_days)
prev_metrics = await self._read_model.metrics(tenant_id, since - period, since)
previous = self._build_kpis(prev_metrics, settings, period_days)
insights = detect_insights(kpis, target_food_cost_bps=target, previous=previous)
```

### WASTE_VALUATION (para Mermas %)
```python
# SOURCE: backend/app/infrastructure/persistence/advisor_repo.py:27-104
select(func.coalesce(func.sum(StockMovementORM.qty * IngredientORM.unit_cost_amount), 0))
  .select_from(StockMovementORM)
  .join(IngredientORM, IngredientORM.id == StockMovementORM.ingredient_id)
  .where(StockMovementORM.tenant_id == tenant_id,
         StockMovementORM.reason == MovementReason.WASTE.value,
         StockMovementORM.created_at >= since, StockMovementORM.created_at <= until)
# qty está en milésimas (QUANTITY_SCALE=1000) → dividir por 1000 al multiplicar por costo.
```

### MIGRATION_RLS
```python
# SOURCE: backend/alembic/versions/0011_advisor_settings.py:1-50 (y 0013 para multi-tabla)
revision = "00XX_<slug>"; down_revision = "0014_payment_tip"
APP_ROLE = "bravo_app"; RLS_TABLES = ("<tabla>",); _NEW_TABLES = [<ORM>.__table__]
def upgrade():
    bind = op.get_bind(); Base.metadata.create_all(bind=bind, tables=_NEW_TABLES)
    op.execute(f"GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO {APP_ROLE};")
    for t in RLS_TABLES:
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""CREATE POLICY tenant_isolation ON {t}
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);""")
# Columna additiva (sin tabla nueva): op.execute("ALTER TABLE x ADD COLUMN IF NOT EXISTS ...")
```

### CONTAINER_PROVIDER
```python
# SOURCE: backend/app/container.py:846-865
finance_overview_read_model = providers.Factory(
    SqlAlchemyFinanceOverviewReadModel, session_factory=db.provided.session)
get_finance_overview = providers.Factory(
    GetFinanceOverview, read_model=finance_overview_read_model, tenant_context=tenant_context)
```

### PRESENTATION_ENDPOINT
```python
# SOURCE: backend/app/presentation/api/v1/analytics.py:28-46
@router.get("/overview", response_model=FinanceOverviewResponse)
@inject
async def get_overview(
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetFinanceOverview = Depends(Provide[Container.get_finance_overview]),
) -> FinanceOverviewResponse: ...
```

### FRONTEND_API_CLIENT + HOOK
```typescript
// SOURCE: frontend/src/api/analytics-api.ts:10-50 + hooks/use-analytics.ts:6-41
export class FinanceApi {
  constructor(private http: HttpClient) {}
  overview(q: FinanceQuery = {}): Promise<FinanceOverviewDTO> {
    return this.http.request("GET", `/finance/overview${this.period(q)}`, { auth: true })
  }
}
export function useFinanceOverview(q: FinanceQuery) {
  const { financeApi } = useServices()
  return useQuery({ queryKey: ["finance-overview", q], queryFn: () => financeApi.overview(q) })
}
```

### SERVICE_REGISTRATION_3_FILES
```typescript
// 1) services/services-context.ts:24-52 → agregar `financeApi: FinanceApi` a interface Services
// 2) services/services-provider.tsx:26-57 → `financeApi: new FinanceApi(http)`
// 3) test/test-utils.tsx:33-68 → `financeApi: {} as unknown as Services["financeApi"]`
```

### ROUTER + NAV
```typescript
// SOURCE: app/router.tsx:74-87 (grupo OWNER/MANAGER) → { path: "/app/finanzas", element: <FinancePage /> }
// SOURCE: components/shell/nav-config.ts:40-69 → { label: "Finanzas", to: "/app/finanzas", icon: <icon>, roles: ["OWNER","MANAGER"] }
```

### TEST_E2E
```python
# SOURCE: backend/tests/integration/test_e2e_advisor.py:13-74
async def test_finance_overview(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    await _sell_with_recipe(http, h, price=150000, qty=2, food_cost_per_kg=80000)
    body = (await http.get("/api/v1/finance/overview", headers=h)).json()
    assert body["kpis"]["food_cost_amount"] == 32000
```

---

## NOT Building (fuera de alcance)
- Métricas de vanidad que el doc descarta: ticket promedio aislado, ROI mensual, cubiertos servidos, growth vs año anterior sin ajustar inflación.
- Integración contable / exportación a contador (eso es Fase 10).
- Predicción/forecast con IA del estilo "5-Out" (sólo la **proyección de cierre por run-rate** del doc, que es aritmética, no ML).
- Reemplazar caja/propinas/arqueo (se **linkean** desde Finanzas, no se reescriben).
- OCR de facturas de proveedores (xtraCHEF) — no está en la spec prescriptiva.

---

## Tandas (cada una: branch → validar → commit → merge --no-ff → push)

### Tanda A — Pantalla unificada + selector temporal + comparativos + diagnósticos
**Entrega:** `/app/finanzas` con los KPIs que **ya tienen data** (Prime Cost, Food %, Labor % [config], Margen de contribución $/producto, Mermas %, net margin, break-even), cada uno con **Δ vs período previo** y rango sano coloreado; los diagnósticos narrados del advisor; selector **Hoy/Semana/Mes/Trimestre/Comparar**. Diseña el contrato `FinanceOverviewReadModel` (port) que Tanda F reimplementará con snapshots.

- **Backend**
  - `application/finance/read_models.py` (CREATE): `FinanceOverview`/`FinanceKpi` (frozen dataclass; cada KPI con `value`, `previous`, `delta`, `healthy_low`/`healthy_high` en bps) + port `FinanceOverviewReadModel`. MIRROR: READ_MODEL_PORT_DTO.
  - `application/finance/use_cases.py` (CREATE): `GetFinanceOverview` (delega + compone advisor KPIs + márgenes por producto + deltas vs previo). MIRROR: USE_CASE_DELEGATES_READ_MODEL y ADVISOR_PREVIOUS_PERIOD_COMPARISON (reusar `_build_kpis`/`detect_insights`).
  - `infrastructure/persistence/finance_repo.py` (CREATE): `SqlAlchemyFinanceOverviewReadModel` que computa en vivo reusando los read models existentes (revenue, product-performance, advisor metrics). MIRROR: SQL_AGGREGATION_WITH_WINDOW.
  - `presentation/api/v1/finance.py` + `schemas/finance.py` (CREATE): `GET /finance/overview?from=&to=` roles OWNER/MANAGER. MIRROR: PRESENTATION_ENDPOINT. Registrar router en `main.py`.
  - `container.py` (UPDATE): providers `finance_overview_read_model` + `get_finance_overview`. MIRROR: CONTAINER_PROVIDER.
- **Frontend**
  - `lib/finance-range.ts` (CREATE): convierte "Hoy/Semana/Mes/Trimestre" → `{from,to}` ISO en hora local; "Comparar" expone dos rangos.
  - `api/finance-api.ts` + `hooks/use-finance.ts` (CREATE) + registro en 3 archivos. MIRROR: FRONTEND_API_CLIENT + SERVICE_REGISTRATION_3_FILES.
  - `features/finance/finance-page.tsx` (CREATE): selector + grilla de `KpiCard` (cada uno con Δ y color por rango sano) + sección de diagnósticos (reusa el render de insights del advisor) + tabla de margen por producto. Ruta `/app/finanzas` (router) + nav "Finanzas" (OWNER/MANAGER). MIRROR: advisor-page + analytics-page.
- **Tests:** e2e `test_e2e_finance.py` (overview con receta → food/labor/prime/margen/deltas); unit del cálculo de deltas/rango sano; front: finance-api test + finance-range test.
- **VALIDATE:** backend ruff+mypy+pytest; front eslint+vitest+build.

### Tanda B — Proyección de cierre mensual + drill-down progresivo
**Entrega:** banner "Si seguís así, cerrás en $X" (run-rate del mes en curso) y drill-down general → producto → ítems (≤3 clics).
- **Backend:** extender `FinanceOverview` con `projection` (proyección lineal: acumulado × días_mes/días_transcurridos, sólo cuando el rango = mes en curso). Endpoint de detalle por producto (`GET /finance/products/{id}` → sus líneas de venta) reusando `sale_facts`.
- **Frontend:** banner de proyección; navegación drill-down (KPI → tabla área → detalle), respetando ≤3 clics.
- **Tests:** unit de la proyección (run-rate); e2e del detalle por producto.

### Tanda C — Diagnostics cacheados (capa 3 del doc; resuelve Fase 9.1)
**Entrega:** los textos narrados (insights + summary LLM) se generan **una vez** ante un cambio relevante y se sirven instantáneos; no se llama a la IA en cada apertura.
- **Backend:** tabla `advisor_diagnostics` (tenant_id + period_key + input_hash + payload JSON + generated_at) con **RLS** (migración 0015, MIRROR: MIGRATION_RLS). `GetFinanceOverview`/advisor: si el `input_hash` (hash de métricas+settings del período) coincide con el cacheado → devolver el payload; si no → regenerar (narrator/synthesizer), guardar, devolver. Invalidación: el hash cambia solo cuando cambian las métricas → no hace falta invalidar a mano, pero exponer un rebuild manual.
- **Tests:** e2e que el segundo request no regenera (mismo `generated_at`); que un cobro nuevo cambia el hash y regenera.

### Tanda D — Labor Cost desde horas reales del fichaje
**Entrega:** Labor % "sensible a horas extras y eficiencia de turnos": labor = Σ(horas fichadas × valor/hora) por empleado, con fallback al costo mensual configurado cuando falta data.
- **Backend:** agregar `hourly_rate_amount` a usuarios (columna additiva en `users`, migración 0016) + endpoint para setearlo (OWNER/MANAGER). `LaborCostReadModel` que cruza `StaffReportReadModel` (worked_minutes + overtime) con el valor/hora; integrarlo en `GetFinanceOverview` reemplazando el labor prorrateado cuando hay rates. MIRROR: staff_report_repo (horas) + advisor settings (fallback).
- **Frontend:** input de valor/hora por empleado (en gestión de equipo); el KPI Labor % pasa a reflejar horas reales.
- **Tests:** unit del cálculo labor=horas×rate + fallback; e2e con turnos cerrados.

### Tanda E — RevPASH + Rotación de inventario (KPIs que faltan + data nueva)
**Entrega:** los 2 KPIs restantes para completar los 7.
- **Backend:**
  - `tables.seating_capacity` (columna additiva, migración 0017) + horario de apertura del tenant (`tenants.opening_hours` o tabla de horarios) para horas-asiento disponibles. **RevPASH** = ventas / (Σ asientos × horas abiertas en el rango).
  - **Rotación de inventario** = COGS del período / valor promedio de inventario. COGS = Σ movimientos SALE valorizados; valor inventario = Σ `stock_qty × unit_cost_amount / 1000`. MIRROR: WASTE_VALUATION (misma técnica qty×costo).
  - Ambos entran en `FinanceOverview`.
- **Frontend:** carga de asientos por mesa + horario; los 2 KPICard nuevos.
- **Tests:** unit de RevPASH y rotación; e2e con mesas con capacidad + horario.

### Tanda F — Capa de snapshots (capa 2 del doc; performance a escala)
**Entrega:** lecturas <100ms independientes del historial. Mismo contrato `FinanceOverviewReadModel`, implementación nueva sobre snapshots diarios.
- **Backend:** tabla `finance_daily_snapshots` (tenant_id + day + totales: sales, food_cost, labor, waste, orders, units, etc.) con **RLS** (migración 0018). Actualización incremental al ocurrir la transacción (en el mismo punto donde hoy se proyecta `sale_facts` — `ProjectOrderSales` y los movimientos de stock/egresos). `SqlAlchemyFinanceSnapshotReadModel` agrega por día (suma de snapshots del rango) en vez de escanear `sale_facts`. Selector de implementación por config/flag para poder comparar/migrar. Comando de rebuild de snapshots (como `RebuildSalesFacts`).
- **Tests:** e2e que el snapshot coincide con el cálculo live (paridad) y que un cobro nuevo actualiza el snapshot del día.

---

## Files to Change (resumen por tanda)
| Tanda | CREATE | UPDATE |
|---|---|---|
| A | `application/finance/{read_models,use_cases}.py`, `infrastructure/persistence/finance_repo.py`, `presentation/api/v1/finance.py`, `presentation/schemas/finance.py`, `frontend/{api/finance-api.ts,hooks/use-finance.ts,lib/finance-range.ts,features/finance/finance-page.tsx}`, tests | `container.py`, `main.py`, `services-context.ts`, `services-provider.tsx`, `test-utils.tsx`, `app/router.tsx`, `nav-config.ts` |
| B | endpoint detalle producto, tests | `finance` read model/use case/page (proyección + drill-down) |
| C | migración 0015, `advisor_diagnostics` repo/tabla, tests | advisor report / finance use case (cache) |
| D | migración 0016, `LaborCostReadModel`, endpoint valor/hora, tests | `users` ORM, finance use case, gestión de equipo (front) |
| E | migraciones 0017, RevPASH/turnover read models, tests | `tables`/`tenants` ORM, finance use case/page |
| F | migración 0018, `finance_daily_snapshots`, snapshot read model + updater, rebuild, tests | `ProjectOrderSales` / puntos de proyección, container (selector de impl) |

---

## Testing Strategy
| Test | Input | Expected | Edge |
|---|---|---|---|
| Food/Labor/Prime en overview | venta con receta + settings | ratios bps correctos | sin receta → food_cost 0 |
| Δ vs período previo | 2 períodos con ventas distintas | delta firmado correcto | período previo vacío → delta = valor actual |
| Rango sano | KPI dentro/fuera del rango | flag healthy/alert | exactamente en el límite |
| Proyección cierre | mitad de mes | acumulado × (días_mes/días_transcurridos) | día 1 → no dividir por 0 |
| Diagnostics cache | 2 requests sin cambios | mismo `generated_at` | cambia una venta → regenera |
| Labor desde horas | turnos cerrados + rate | Σ horas×rate | sin rate → fallback config |
| RevPASH | asientos+horario+ventas | ventas/(asientos×horas) | 0 asientos/horas → 0, no div0 |
| Rotación | COGS + inventario | COGS/valor_inv | inventario 0 → 0, no div0 |
| Snapshot paridad | mismas ventas | snapshot == live | sin transacciones → ceros |
| RLS | dos tenants | cada uno ve solo lo suyo | — |

### Edge Cases Checklist
- [ ] Sin ventas / sin recetas / sin settings (todo 0, sin crashear)
- [ ] División por cero (RevPASH, rotación, ratios, proyección día 1)
- [ ] Período previo vacío (deltas)
- [ ] Tenant aislado (RLS) en cada tabla nueva
- [ ] `tenant_context.set()` antes de cada lectura (defensa en profundidad sobre RLS)
- [ ] Money no-negativo donde aplique; bps enteros (sin floats)

---

## Validation Commands

### Backend (en `backend/`)
```bash
poetry run ruff check app tests
poetry run mypy app
poetry run pytest -q
```
EXPECT: ruff/mypy limpios; toda la suite verde.

### Migraciones (en `backend/`)
```bash
set -a; . ./.env; set +a
poetry run alembic upgrade head
poetry run alembic downgrade -1 && poetry run alembic upgrade head   # reversibilidad
```
EXPECT: migración aplica y revierte sin error.

### Frontend (en `frontend/`)
```bash
npx eslint <archivos-tocados>
npm run build         # tsc -b && vite build — GATE REAL (no usar tsc --noEmit)
npx vitest run
```
EXPECT: eslint 0 errores; build verde; vitest verde.

### Manual
- [ ] `! npm run dev` → `/app/finanzas` muestra los KPIs con Δ y selector temporal
- [ ] Cambiar el rango (Hoy/Semana/Mes/Trim) recalcula
- [ ] Un cobro nuevo mueve los números y (Tanda C) regenera el diagnóstico

---

## Acceptance Criteria
- [ ] Los 7 KPIs del doc presentes y correctos (Prime, Food%, Labor%, Margen $/producto, RevPASH, Mermas%, Rotación)
- [ ] Comparativos vs período previo visibles en cada KPI
- [ ] Proyección de cierre mensual
- [ ] Diagnósticos en lenguaje natural, cacheados (no se llama a la IA por request)
- [ ] Drill-down general→área→ítem en ≤3 clics
- [ ] Selector temporal Hoy/Semana/Mes/Trimestre/Comparar
- [ ] Capa de snapshots con paridad vs live
- [ ] Todas las validaciones pasan; RLS por tenant en cada tabla nueva

## Completion Checklist
- [ ] Sigue los patrones descubiertos (read model, advisor, RLS, React Query)
- [ ] Errores con `code` EN + `message` ES (registrados en `presentation/errors.py`)
- [ ] Código en inglés, UX en español
- [ ] Tests 80%+ en dominio/casos de uso
- [ ] Sin valores hardcodeados; bps enteros, Money en unidades mínimas
- [ ] Untracked `backend/scripts/`, `drive-download-*`, `Pantalla Finanzas .md` NO se commitean

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Doble fuente de verdad (snapshots vs live divergen) | Media | Alto | Test de paridad obligatorio (Tanda F) + comando de rebuild |
| Labor desde horas incompleto (no todos fichan / sin rate) | Alta | Medio | Fallback al costo configurado; marcar el KPI como "estimado" si falta data |
| RevPASH/rotación con data nueva que el tenant no carga | Alta | Medio | Mostrar el KPI como "configurá asientos/horario" en vez de 0 engañoso |
| Caché de diagnostics sirve algo viejo | Media | Medio | `input_hash` de métricas+settings → invalida solo cuando cambian los datos |
| Inflación AR distorsiona comparativos | Media | Medio | El doc lo marca; comparar en términos reales o avisar (follow-up, no bloquea) |
| Scope XL en un solo pasaje | Alta | Alto | 6 tandas independientes mergeables; cada una valida y mergea sola |

## Notes
- **Orden recomendado:** A → B → C → D → E → F. A entrega valor visible ya; F (performance) va al final pero su contrato se diseña en A.
- El **advisor (Fase 9)** es el motor; esta fase lo **envuelve y completa**, no lo reescribe. Reusar `_build_kpis`, `detect_insights`, narrator/synthesizer.
- Mermas: el advisor calcula el ratio sobre food cost; **el doc pide sobre facturación** (<3%) → usar `waste/sales` en la Pantalla Finanzas.
- Deploy: las migraciones se aplican solas en Railway (`preDeployCommand: alembic upgrade head`).
- 🔴 Pendiente de seguridad (no de esta fase): rotar contraseña DB + API key Anthropic.
```
