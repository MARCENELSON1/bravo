# Implementation Report: Productos v3 — Fase 3 (Estado confirmado + cobertura)

## Summary
"Cero plata sobre costos inventados." Cada plato tiene un estado **estimado/
confirmado** y una **cobertura** de costo, y las pantallas etiquetan/grisan/excluyen
los estimados de las conclusiones de plata — **sin ocultarlos**. Metadata + read
model + display: **`costing.py` matemático intacto → paridad por construcción**;
**sin migración, sin DI**.

## Diseño
- **Confirmación DERIVADA** (sin flag, sin migración): un insumo está confirmado ⇔
  tiene ≥1 compra real (movimiento PURCHASE). El costo solo se mueve por compra →
  exacto, sin drift.
- **Cobertura** = food cost confirmado / bruto, con un **tercer mapa** de costo en
  `food_cost_repo` (los no confirmados aportan 0), reusando `food_cost`/
  `resolve_preparation_costs` — el mismo doble-cómputo bruto/neto ya existente.
- **Display honesto (Regla 6):** etiquetar (badge estimado/confirmado), grisar la
  plata de los estimados, excluirlos del hero/totales — nunca ocultar.

## Backend (`3df735a`)
- `coverage_bps()` puro en `costing.py` (gemelo de `food_cost_ratio_bps`);
  constantes `CONFIRMED_PLATE_BPS=10000` / `COVERAGE_GATE_BPS=7000`.
- `FoodCostRow` +`cost_confirmed`/`coverage_bps`; `FoodCostReport` +`coverage_bps`/
  `confirmed_count`/`total_count`; `GET /inventory/food-cost` los expone.
- Read model: query PURCHASE tenant-scoped → `confirmed_ids` + mapa confirmado +
  resolución de preparaciones confirmadas + agregación del reporte.

## Frontend (`dd48709` catálogo/Ficha + `3d9f3c5` menu engineering)
- Tipos + `catalog-rows` (`costConfirmed`/`coverageBps`; sin receta → confirmado).
- **Catálogo:** badge "estimado" + grisado del "Te deja" (tooltip con % confirmado).
- **Ficha:** badge Costo confirmado/estimado + "N% respaldado por compras".
- **Menu engineering:** `classifyMenu(rows, estimatedIds?)` (opcional → paridad; sin
  receta = no estimado); `topEarners`/`confirmedMargin` excluyen estimados; línea
  "N de M platos con costo confirmado"; MenuRow grisa el margen + badge.

## Validación
| Level | Status |
|---|---|
| Backend tests | ✅ 431 passed (5 nuevos: 4 coverage_bps + 1 e2e) |
| Backend ruff | ✅ clean |
| Frontend build/lint | ✅ |
| Frontend tests | ✅ 151 passed (3 nuevos) |
| Paridad | ✅ suite completa sin cambios de números; sin `estimatedIds`/todo-confirmado == hoy |

Se hizo en backend → frontend slices, validando cada uno. Backend primero (parity-
safe) mientras se hacía la revisión visual de la Ficha; frontend después, sobre UI
ya verificada.

## Diferido (documentado, no fabricado)
- **Costo estimado por IA con desglose** (T1.7 prioridad Could, reusa LLM Fase 9).
- **Gate ≥70% del hero** ("te faltan N platos") → **Fase 6** (esta tanda deja
  `report.coverage_bps`/`confirmed_count`/`total_count` listos para que el hero los
  consuma).
- Flag/estado almacenado (`cost_confirmed` en Ingredient) → cuando exista confirmar-
  a-mano o costo por IA (ahí un enum `ESTIMATED/CONFIRMED/AI_ESTIMATED`).

## Próximo
Fase 6 (hero con gate ≥70%), menu engineering por categoría, CRM (Fase 12).
