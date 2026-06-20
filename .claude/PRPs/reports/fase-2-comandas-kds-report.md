# Implementation Report: Fase 2 — Comandas + KDS

## Summary
Primer módulo del motor operativo de NÚCLEO: captura de la comanda digital (mozo) y su visualización en cocina (KDS web, cuasi tiempo real por polling). Agrega el dominio `Table`/`Product`/`Order`/`OrderItem` sobre la Clean Arch + multi-tenant + RLS de la Fase 1, e introduce el value object transversal `Money` (entero en unidad mínima + ISO-4217) y la config país/moneda por tenant. Implementado de punta a punta (backend + frontend), validado y pusheado.

## Assessment vs Reality

| Metric | Predicted (Plan) | Actual |
|---|---|---|
| Complexity | XL | XL (confirmado) |
| Confidence | 7/10 | Implementado en una pasada (en 2 tramos: backend → frontend) |
| Files Changed | ~45 | **66** (46 backend + 20 frontend), +2586 / −9 |

## Tasks Completed

| # | Task | Status | Notes |
|---|---|---|---|
| 1 | `Money` VO + excepciones compartidas | ✅ | `domain/shared/money.py` (entero + ISO-4217) |
| 2 | Tenant: país/moneda | ✅ | `country`/`currency` (default AR/ARS) en entidad + ORM + migración |
| 3 | Dominio `Table` / `Product` | ✅ | entidades, ports, excepciones |
| 4 | Dominio `Order` (agregado + máquina de estados) | ✅ | OPEN→SENT→PREPARING→READY→SERVED (+CANCELLED) |
| 5 | Registrar excepciones en el handler | ✅ | `presentation/errors.py` |
| 6 | ORM models + mappers | ✅ | `tables/products/orders/order_items` + tenant cols; **BigInteger** para montos |
| 7 | Repositorios SQLAlchemy | ✅ | tenant-scoped; agregado Order+items (load/save con sync) |
| 8 | Migración Alembic 0002 (+ RLS) | ✅ | up/down/up verificado; policy `tenant_isolation` en las 4 tablas |
| 9 | Casos de uso (application) | ✅ Deviated | agrupados por módulo (`use_cases.py`) en vez de un archivo por caso |
| 10 | Schemas + routers + container + main | ✅ | routers products/tables/orders/kds con RBAC |
| 11 | Fakes + unit tests de use cases | ⚠️ Deviated | cubierto por los tests de integración e2e (no se agregaron fakes/unit dedicados) |
| 12 | Integration e2e (DB real + RLS) | ✅ | ciclo comanda→KDS + comanda vacía + aislamiento RLS |
| 13 | Frontend: clientes + DI + tipos + money | ✅ | orders/products/tables-api inyectables + `formatMoney` |
| 14 | Frontend: hooks | ✅ | TanStack; `use-kds-orders` con `refetchInterval: 5000` |
| 15 | Frontend: pantallas + router + guards | ✅ Deviated | ruta `/app/orders/:orderId` (no `:tableId`) |
| 16 | Frontend: tests + cierre | ✅ | money + orders-api |

## Validation Results

| Level | Status | Notes |
|---|---|---|
| Static Analysis (backend) | ✅ Pass | `ruff` + `mypy` (103 source files) |
| Static Analysis (frontend) | ✅ Pass | `tsc -b` + `eslint` |
| Unit + Integration (backend) | ✅ Pass | **66 tests** (incluye e2e con DB real) |
| Tests (frontend) | ✅ Pass | **14 tests** (vitest) |
| Build (frontend) | ✅ Pass | `vite build` |
| DB / Migration | ✅ Pass | `alembic upgrade head` → `downgrade -1` → `upgrade head` |
| Edge Cases | ✅ Pass | comanda vacía → `empty_order`; aislamiento RLS entre tenants; transiciones inválidas |

## Files Changed (resumen)

| Área | Archivos | Acción |
|---|---|---|
| `backend/app/domain/{shared,table,product,order}` | entidades/VOs/excepciones/ports | CREATE |
| `backend/app/domain/tenant/entities.py` | +country/currency | UPDATE |
| `backend/app/infrastructure/persistence/{models,mappers}.py` | +4 ORM + mappers | UPDATE |
| `backend/app/infrastructure/persistence/{table,product,order}_repo.py` | repos | CREATE |
| `backend/alembic/versions/0002_orders_kds.py` | migración + RLS | CREATE |
| `backend/app/application/{table,product,order}/` | dtos + use_cases | CREATE |
| `backend/app/presentation/{schemas,api/v1}/{products,tables,orders,kds}.py` | schemas + routers | CREATE |
| `backend/app/{container,main}.py`, `presentation/errors.py` | wiring + handler | UPDATE |
| `backend/tests/{unit,integration}` | test_money/test_order + e2e_orders + conftest | CREATE/UPDATE |
| `src/api/{types-operations,products-api,tables-api,orders-api}.ts`, `lib/money.ts` | datos | CREATE |
| `src/hooks/use-{products,tables,orders,kds-orders}.ts` | hooks | CREATE |
| `src/features/{floor,orders,kds,products}/*.tsx` | pantallas | CREATE |
| `src/services/services-{context,provider}`, `app/router.tsx`, `features/identity/home-page.tsx`, `test/test-utils.tsx` | wiring | UPDATE |

**Total:** 66 archivos (46 backend / 20 frontend), +2586 / −9.

## Deviations from Plan
1. **Casos de uso agrupados por módulo** (`application/<m>/use_cases.py`) en vez de un archivo por caso (estilo Fase 1) — reduce archivos; misma semántica.
2. **Task 11 (fakes + unit de use cases) cubierto por los e2e de integración** en lugar de tests unitarios dedicados con fakes. El dominio sí tiene unit tests (`test_money`, `test_order`); los use cases se ejercitan end-to-end con DB real. Trade-off consciente por presupuesto/tiempo.
3. **`GetOrder` use case agregado** (no listado explícito en el plan) para `GET /orders/{id}`; las mutaciones devuelven la `Order` para que los routers respondan el estado actualizado.
4. **Ruta de comanda `/app/orders/:orderId`** (no `:tableId`): la comanda se crea al tocar la mesa en el floor y se navega por su id.
5. **Montos en DB como `BigInteger`** (entero en unidad mínima), anulando la sugerencia de `DECIMAL` del explorador — alineado con la decisión multi-moneda del PRD.

## Issues Encountered
- Ruff pidió reordenar imports en `errors.py`/`container.py` tras los agregados → `ruff --fix` (idempotente).
- `test-utils` del front: `Services` ganó 3 clientes nuevos → se agregaron stubs (`{} as unknown as ...`) para no romper los tests de identidad (que no los usan).
- Ninguno bloqueante.

## Tests Written

| Test File | Tests | Cobertura |
|---|---|---|
| `backend/tests/unit/test_money.py` | 6 | Money: normalización, suma, mismatch, negativos, moneda inválida |
| `backend/tests/unit/test_order.py` | 5 | lifecycle, transiciones inválidas, comanda vacía, total |
| `backend/tests/integration/test_e2e_orders.py` | 3 | ciclo comanda→KDS, comanda vacía (422), aislamiento RLS |
| `src/lib/money.test.ts` | 2 | `formatMoney` |
| `src/api/orders-api.test.ts` | 3 | body de create/addItem, endpoint KDS |

## Next Steps
- [ ] Crear PRs (Fase 1 y Fase 2) — `gh` sin auth; `! gh auth login` y se arman.
- [ ] `/code-review` de la rama (opcional, recomendado).
- [ ] **Fase 3 — Cobro + Pagos**: `/prp-plan .claude/PRPs/prds/nucleo.prd.md` (toma la próxima fase pendiente).

---

*Branch: `feat/fase-2-comandas-kds` (pusheada). Commits: `eaf3956` (dominio) · `d4d08d2` (backend) · `92175a0` (frontend) · `c89ff99` (docs).*
