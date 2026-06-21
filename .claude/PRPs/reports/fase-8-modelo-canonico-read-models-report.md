# Implementation Report: Fase 8 — Modelo canónico + read models (CQRS-lite, medallion-lite en Postgres)

## Summary
El puente captura → inteligencia. Capa analítica **medallion-lite dentro del mismo Postgres**: **silver** =
`sale_facts` (fact table canónica con RLS, mantenida por **proyección transaccional** al pasar la comanda a PAID,
generalizando el hook de Fase 6); **gold** = read models de KPIs detrás de ports (ingresos, ventas, egresos,
**margen bruto**, ticket promedio, **mix de medios de pago**, top productos). Endpoints `/analytics/*` + página
Analítica en pesos. Es la base estable que después consumen el asesor y el copiloto (Capa 2). Prioridad PRD: *Should*.

## Assessment vs Reality

| Metric | Predicted (Plan) | Actual |
|---|---|---|
| Complexity | Media (proyección reusa Fase 6; lo fino es el vocabulario canónico) | Coincide — push idéntico al patrón de inventory |
| Confidence | Alta T1/T3, Media T2 | Confirmado; T2 salió sin scope creep (KPIs base) |
| Files Changed | ~25 nuevos/editados | 30 archivos (1525+ líneas) |

## Tasks Completed

| # | Task | Status | Notes |
|---|---|---|---|
| T1 | Silver: sale_facts + proyección transaccional | ✅ Complete | Projector idempotente + rebuild; migración 0010; 3 e2e |
| T2 | Gold: read models de KPIs + API | ✅ Complete | revenue/payment-mix/products + /analytics/*; 5 e2e |
| T3 | Frontend: página Analítica | ✅ Complete | KPIs en pesos + mix + top productos; 7 tests |
| T4 | No-shows / covers (opcional) | ⏭️ Diferido | A Fase 9 (es dimensión del asesor, no KPI base del *Success*) |

## Validation Results

| Level | Status | Notes |
|---|---|---|
| Static Analysis | ✅ Pass | ruff + mypy (216 archivos) limpios; tsc + eslint limpios |
| Unit Tests | ✅ Pass | costing/dominio reusados; lib frontend 3 |
| Build | ✅ Pass | `vite build` ok (warning de chunk preexistente) |
| Integration (e2e) | ✅ Pass | 8 e2e backend (3 proyección + 5 gold) + 4 api frontend |
| Edge Cases | ✅ Pass | idempotencia re-settle, snapshot food cost, rebuild backfill, RLS, sin recetas |
| Coverage | ✅ Pass | analytics aplicación 96% (≥80% requerido) |

## Files Changed (30)
**Backend nuevos:** `application/analytics/{__init__,facts,ports,projection,rebuild,read_models,use_cases}.py`,
`infrastructure/persistence/{sale_facts_repo,analytics_repo}.py`, `presentation/api/v1/analytics.py`,
`presentation/schemas/analytics.py`, `alembic/versions/0010_sale_facts.py`,
`tests/integration/test_e2e_analytics.py`.
**Backend editados:** `models.py`, `container.py`, `main.py`, `application/payment/use_cases.py` (segundo hook
post-PAID), `tests/integration/conftest.py`.
**Frontend nuevos:** `api/{types-analytics,analytics-api,analytics-api.test}.ts`, `hooks/use-analytics.ts`,
`lib/{analytics,analytics.test}.ts`, `features/analytics/analytics-page.tsx`.
**Frontend editados:** `services/services-{context,provider}.tsx`, `test/test-utils.tsx`,
`components/shell/nav-config.ts`, `app/router.tsx`.

## Deviations from Plan
1. **Los 3 read models de gold en un solo `analytics_repo.py`** (el plan listaba 3 archivos
   `{revenue,payment_mix,product_performance}_repo.py`). Son cohesivos: misma fuente (`sale_facts`/`payments`) y
   misma semántica de período. Cada read model sigue siendo su propia clase detrás de su port.
2. **Mapping de `SaleFact` inline en `sale_facts_repo.py`** (no en `mappers.py`), igual que `food_cost_repo`: la
   `SaleFact` es un DTO de la capa analítica, no una entidad de dominio.
3. **T4 (no-shows/covers) diferido** a Fase 9 — no entra en el *Success* del MVP (ingresos/egresos/margen/ticket/
   medios); las reservas/no-shows ya están capturadas (Fase 7) y se proyectan cuando el asesor las necesite.

## Issues Encountered
- **Segundo colaborador post-PAID:** `_settle_order` ahora dispara dos hooks opcionales (inventory + sales), ambos
  detrás de un port e idempotentes. Se resolvió con un segundo parámetro opcional (no se necesitó una lista de hooks).
- **Orden de providers:** `sale_facts_repository` + `project_order_sales` se definen **antes** de la sección de
  pagos (el settle los inyecta), igual que se hizo con el `InventoryConsumer`.
- **Verificación de la proyección sin API de lectura en T1:** se asertó vía el `admin_engine` (bypassa RLS),
  contando filas de `sale_facts`; los KPIs de T2 ya se ejercitan por HTTP.

## Tests Written

| Test File | Tests | Coverage |
|---|---|---|
| `tests/integration/test_e2e_analytics.py` | 8 | proyección+idempotencia+snapshot, revenue, mix, productos, rebuild, RLS |
| `frontend/src/api/analytics-api.test.ts` | 4 | revenue query, sin período, limit, rebuild POST |
| `frontend/src/lib/analytics.test.ts` | 3 | labels de medio/dirección |

## Next Steps
- [ ] Code review via `/code-review`
- [ ] Merge a `main` (rama `feat/fase-8-modelo-canonico`)
- [ ] (Operación) tras deploy, `POST /analytics/rebuild` por tenant para backfillear las comandas PAID previas
- [ ] **Fase 9 — Asesor financiero + Dashboard**: ahora hay modelo canónico que consumir (KPIs, no-shows, food cost)
