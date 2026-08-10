# Implementation Report: Productos v3 — Fase 2D (Versionado + costo de reposición)

## Summary
Cierra la Fase 2 de Productos v3 (2A merma / 2B IVA / 2C conversión / 2D). A
diferencia de 2A/2B/2C, **2D NO toca `costing.py`**: es metadata + read models
sobre datos ya congelados (`sale_facts`) y ya capturados (`stock_movements`) → la
paridad es por construcción (la más fuerte de las cuatro tandas). El análisis
previo confirmó que 2D estaba ~80% cubierto por infraestructura existente; se
implementó el **delta mínimo**, sin fabricar feature.

## T1.6 — Versionado de receta
- `Recipe.version: int = 1`; `SetRecipe` lee la receta actual e incrementa (nueva
  → v1, edición → previa+1).
- `sale_facts.recipe_version` snapshoteado por venta en `ProjectOrderSales` (None
  si el producto no tiene receta). **No toca el cálculo de food cost** — que ya se
  congelaba (`food_cost_amount`/`food_cost_net_amount`).
- `RecipeResponse.version` expuesto.
- **Valor**: atribución/auditoría (distinguir "cambió la receta" de "subió el
  insumo"), NO exactitud — la exactitud histórica ya la da `sale_facts`. El
  consumo (gráficos, "ver receta como estaba") es Fase 7.

## T1.4 — Costo de reposición + histórico de insumo
- **Reposición = último precio: YA es el default** (`Ingredient.set_cost` en cada
  compra). Cero código de motor; se fija con un test (2ª compra más cara → sube el
  food cost al costo de reposición).
- **Histórico de costo de insumo** desde `stock_movements` (compras), **sin tabla
  nueva**: port `IngredientCostHistoryReadModel` + DTO `IngredientCostPoint` + use
  case `GetIngredientCostHistory` + `GET /inventory/ingredients/{id}/cost-history`.

## T1.5 — Tope de profundidad (DIFERIDO a propósito)
Los ciclos ya están guardados (`RecipeCycle` en `costing.py`). Un cap de
profundidad explícito es puramente defensivo contra un anidamiento **acíclico** >5
niveles (no es un riesgo real) y tocaría `costing.py` — que se mantiene byte por
byte igual para preservar la paridad del motor. Diferido.

## Migración
- `0027_recipe_version` — `recipes.version` (server_default "1", backfill recetas
  viejas a v1) + `sale_facts.recipe_version` (nullable; filas previas = sin versión).

## Validación
| Level | Status |
|---|---|
| Backend tests | ✅ 426 passed |
| Backend ruff (changed) | ✅ clean |
| Migración (dev) | ✅ 0027 aplicada |
| Paridad | ✅ suite completa sin cambios de números (costing.py intacto) |

Hecho en 2 slices (T1.6 versionado → T1.4 histórico/reposición), validando cada
uno con la suite completa como test de paridad. e2e: `test_recipe_version_increments_on_save`
(v1→v2) + `test_replacement_cost_is_last_purchase_with_history` (2ª compra sube food
cost + queda en el histórico).

## Fase 2 de Productos v3 — COMPLETA
2A merma ✅ · 2B IVA ✅ · 2C conversión ✅ · 2D versionado/reposición ✅.

## Diferido / próximo
- Fase 7 (Ficha del producto): display del histórico, gráfico de costo del plato,
  alertas "el bife subió X%", "ver receta como estaba" (consumen el dato que 2D
  deja disponible).
- Snapshot item-level de receta + costeo configurable (promedio ponderado):
  diferidos explícitamente.
- Menu engineering por categoría; CRM (Fase 12).
