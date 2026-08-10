# Implementation Report: Productos v3 — Fase 6 (Hero verificable + gate de cobertura ≥70%)

## Summary
El hero "Tu carta" (menu engineering) solo muestra **conclusiones de plata**
("te dejó $X", "los 3 que más plata te dejan", "Te dejan $X" por categoría) cuando
la **cobertura de costo del tenant llega al umbral** (`COVERAGE_GATE_BPS = 7000`).
Por debajo, las reemplaza por un empty-state honesto — "te faltan N platos con costo
confirmado (vas X de M)" + CTA "Cargar compras" → `/app/stock`. Ethos del proyecto:
**nunca mostrar un número inflado por costos estimados**. Sin migración, sin DI,
`costing.py` intacto → **paridad por construcción**.

## Diseño
- **Umbral una sola vez (Regla 6):** el backend consume `COVERAGE_GATE_BPS` (dominio) y
  expone `coverage_ok: bool`. El front lee el bool, **nunca hardcodea el 70%**.
- **Gate solo en la única superficie inflable:** el hero de Productos. El **Home NO se
  gatea** — su `net` es caja financiera (ventas−egresos), no deriva del food cost.
- **Paridad:** campo aditivo default `True`; sin food cost cargado → `open` (no gatea,
  no parpadea mientras carga). Sin platos (`total_count==0`) → `coverage_bps=10000` →
  `coverage_ok=True` (no hay conclusión que gatear).

## Backend (aditivo, sin migración, sin DI)
- `application/inventory/food_cost.py` — `FoodCostReport +coverage_ok: bool = True`.
- `infrastructure/persistence/food_cost_repo.py` — importa `COVERAGE_GATE_BPS`;
  `coverage_ok = report_coverage >= COVERAGE_GATE_BPS`.
- `presentation/schemas/inventory.py` — `FoodCostResponse +coverage_ok: bool = True`.
- `presentation/api/v1/inventory.py` — mapea `coverage_ok=report.coverage_ok`.

## Frontend
- `api/types-inventory.ts` — `FoodCostReportDTO +coverage_ok: boolean`.
- **CREATE** `features/products/coverage-gate.ts` — helper puro `coverageGate(report?)`
  → `{ open, missing, confirmed, total }` (`open = coverage_ok ?? true`,
  `missing = max(0, total − confirmed)`).
- **CREATE** `features/products/coverage-gate.test.ts` — 4 tests (open true/false,
  missing exacto, sin report → open, nunca negativo).
- `features/products/menu-engineering-view.tsx` — `const gate = coverageGate(foodCost.data)`;
  hero con frase de plata (`confirmedMargin`) si `gate.open`, si no el empty-state + CTA;
  top-earners y "Te dejan $X" per-categoría envueltos en `gate.open`.

## Validación
| Level | Status |
|---|---|
| Backend tests | ✅ 431 passed (+1 assert `coverage_ok is False` en e2e preparaciones @50%) |
| Backend ruff (archivos tocados) | ✅ clean |
| Frontend build | ✅ |
| Frontend lint | ✅ clean |
| Frontend tests | ✅ 155 passed (+4 nuevos de coverage-gate) |
| Paridad | ✅ suite backend sin cambios de números; sin food cost / todo-confirmado == hoy |

Nota: 2 E501 pre-existentes en `tests/integration/test_e2e_finance.py` (no tocado por
esta tanda, fuera de scope).

## Deviations
Ninguna. Implementado exactamente como el plan.

## Diferido
T6 rotación por sobre-índice (otro plan); `gate_bps` en la API (solo si el copy muestra
el objetivo); denominador "todos los productos" (se mantiene el de food-cost = platos
con receta); nudge de cobertura en onboarding sin ventas.

## Próximo
Menu engineering por categoría (Fase 4), Fase 10 Reportes, Fase 11 Copiloto, Fase 12 CRM.
