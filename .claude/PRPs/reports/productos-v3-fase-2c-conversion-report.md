# Implementation Report: Productos v3 — Fase 2C (Conversión de unidades)

## Summary
Un insumo puede **comprarse/costearse en su unidad grande** (KG o L) y **usarse en
receta en la sub-unidad fina de la misma familia** (G o ML) sin perder exactitud.
Campo opcional `Ingredient.recipe_unit` (None = paridad total). El factor de
familia (constante 1000, entero) entra como parámetro **identidad** en el único
`round` de la línea de costo, y en el descuento de stock. Con `recipe_unit=None`
el motor es idéntico al de hoy → **paridad garantizada** (suite completa sin
cambios). Cierra las tandas "de motor" de la Fase 2 (2A merma, 2B IVA, 2C
conversión); queda 2D (versionado + costo de reposición).

**Alcance (según PRD):** KG↔G y L↔ML, factor 1000. Fuera: g↔ml (densidad) y
packs/cajas (no hay unidad CASE).

## Diseño
`recipe_unit` opcional + `factor_by_ingredient` opcional identidad en
`food_cost()`/`resolve_preparation_costs()`. El costo se guarda por unidad de
compra (exacto); la cantidad de receta está en milésimas de `recipe_unit`; la
línea es `round(cost × qty × num / (den × 1000))` con `(num,den)` = `(1,1)` sin
conversión o `(1,1000)` para KG→G / L→ML. Helper puro `recipe_conversion.py`
(`conversion_factor` + `assert_convertible` + `IncompatibleUnits`).

## Los 3 consumidores de `qty` (todos aplican el factor)
- `food_cost_repo` (drill-down / catálogo) y `projection` (→ sale_facts/snapshots):
  los dos builders del food cost.
- `consume.py`: descuenta stock convertido a la unidad base (guard para consumos
  sub-milésima que redondean a 0).

## Decisión v1
`recipe_unit` se setea **solo al crear** (`CreateIngredient` valida con
`assert_convertible`). `UpdateIngredient` **no la cambia** — cambiarla sobre un
insumo ya en recetas reinterpretaría las cantidades ×1000. Adoptar 2C en insumos
existentes (con rescale de sus recetas en la misma transacción) = mejora futura.
**Sin cambios en el DI container** (los 3 consumidores ya tenían el repo de
insumos).

## Migración
- `0026_recipe_unit` — `ingredients.recipe_unit` nullable (NULL = unidad base).
  Filas existentes quedan NULL → recetas actuales intactas.

## Frontend
- `IngredientDTO`/`CreateIngredientBody` con `recipe_unit`; helper
  `recipeUnitOptions` (KG→[kg,g], L→[ml,l], resto vacío).
- `CreateIngredientSheet`: select "Unidad de receta" (solo KG/L, create-only).
- Editor de receta (`ComponentRowsEditor`): etiqueta de unidad por insumo
  (`recipe_unit ?? unit`) para tipear la cantidad en la unidad correcta. La
  matemática (`toMilesimas` ×1000) no cambia: se guarda en milésimas de la unidad
  de receta y el backend convierte.

## Validación
| Level | Status |
|---|---|
| Backend tests | ✅ 424 passed |
| Backend ruff (changed) | ✅ clean |
| Frontend build | ✅ |
| Frontend lint | ✅ |
| Frontend tests | ✅ 143 passed |
| Migración (dev) | ✅ 0026 aplicada |

Se implementó en slices validando cada uno (foundation → data/consumidores → API
→ frontend), con la **suite completa como test de paridad** en cada paso.

- Unit `test_recipe_conversion.py`: factor, validación, paridad (identidad ==
  hoy) y exactitud (kg→g = 465; pizca 0,5 g preserva precisión = 250).
- e2e `test_recipe_unit_converts_food_cost` (litro→ml, food cost 50000) +
  `test_incompatible_recipe_unit_rejected` (422).

## Limitaciones conocidas (documentadas)
- No se puede cambiar `recipe_unit` de un insumo ya creado (v1).
- Precisión sub-milésima del stock en consumos muy chicos (pizca) — stock está
  fuera del alcance del PRD.
- g↔ml y packs quedan fuera (futuro).

## Queda de Fase 2 / Productos v3
2D (versionado de recetas + costo de reposición). Luego: menu engineering por
categoría, y CRM (Fase 12).
