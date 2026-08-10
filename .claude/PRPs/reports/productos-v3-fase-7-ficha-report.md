# Implementation Report: Productos v3 — Fase 7 (Ficha del producto) v1

## Summary
La Ficha del plato como drawer de composición **100% frontend** sobre datos que la
Fase 2 (2A/2B/2C/2D) ya dejó disponibles. **Sin migración, sin `costing.py`, sin
DI.** Confirmó la hipótesis: 6 de 8 fuentes ya estaban E2E; el único gap real era
el cliente frontend del endpoint `cost-history` (construido en 2D).

## Qué se hizo
**Slice 1 — plumbing + lógica pura:**
- `RecipeDTO.version` + `IngredientCostPointDTO` (types).
- `InventoryApi.ingredientCostHistory(id)` + `useIngredientCostHistory(id)` (el
  endpoint backend existía desde 2D; le faltaba el cliente/hook).
- `ficha-logic.ts` (puro, testeable): `costSeriesByDay` (costo del plato en el
  tiempo desde el drill-down congelado) + `ingredientCostAlert` ("subió Y%" +
  stale >60d). 5 tests.

**Slice 2 — componente:**
- `ProductFicha` (`Sheet` on-demand) abierto desde el catálogo, junto al editor de
  receta existente (no lo reemplaza). Secciones: resumen (precio / costo bruto /
  te deja neto / food cost %), receta con desglose + versión, costo del plato en
  el tiempo (sparkline SVG inline, sin dependencia), insumos con alertas.
- `IngredientAlertRow` (sub-componente: histórico de costo por insumo, on-demand).

## Validación
| Level | Status |
|---|---|
| Frontend build | ✅ |
| Frontend lint | ✅ |
| Frontend tests | ✅ 148 passed (5 nuevos) |
| Backend | N/A (no se tocó) |

**PENDIENTE: revisión visual en navegador** — la lógica está testeada y compila/
lintea, pero el layout/UX del drawer + el sparkline no se verificaron visualmente.

## Decisiones / diferidos
- **v1 frontend-only**: el backend opcional (`recipe_version` por línea para marcar
  cambios de receta en el gráfico) se **difirió** para mantenerlo 100% frontend.
- **Precios** no se puso en el drawer (ya viven en la página, `pricing-inflation-card`).
- **Depende de Fase 3** (no mergeada): estado estimado/confirmado + cobertura ≥70%
  → **diferido**, no fabricado. La Ficha v1 muestra los números disponibles.
- Snapshot item-level de receta ("ver receta como estaba") + mano de obra por plato:
  diferidos (PRD).

## Notas
- La Ficha es el **consumidor** del dato que 2D dejó congelado (`sale_facts.recipe_version`,
  histórico en `stock_movements`) — "2D deja la etiqueta; la Ficha la usa".
- Colisión evitada: la lógica pura se llama `ficha-logic.ts` (no `product-ficha.ts`)
  para no chocar con el componente `product-ficha.tsx`.

## Próximo
- Revisión visual de la Ficha.
- Fase 3 (estado estimado/confirmado + cobertura) para completar la Ficha.
- Menu engineering por categoría; CRM (Fase 12).
