# Implementation Report: Productos v2 — Tanda C (recetas madre / food cost multinivel)

**Fecha:** 2026-08-02 · **Ramas:** `feat/productos-v2-c[-wiring|-crud|-frontend]`

## Summary
Tercera y última tanda de Productos v2 (la más riesgosa: toca el motor de food
cost que alimenta Finanzas). Agrega **preparaciones base (recetas madre) con
rendimiento**: un plato puede usar X de una preparación y su costo se prorratea
por lo que rinde, multinivel (una prep puede anidar otra), con **guard anti-ciclo**.
Un cambio de costo de un insumo base **se propaga solo** a todos los platos.
Se hizo en **4 slices**, cada una no-breaking y validada.

## Modelo (fijado con el usuario)
**Preparación base propia con rendimiento** (elegida sobre "producto del catálogo
usado como ingrediente"): entidad nueva aparte del catálogo vendible; costo por
unidad = costo de sus componentes ÷ rendimiento.

## Slices (todas en `main`)
1. **Foundation** (`bdc8081`) — núcleo puro no-breaking: `domain/inventory/recipe.py`
   (`RecipeItem` insumo XOR `preparation_id`; entidad `Preparation` con `yield_qty`),
   `costing.py` (`food_cost()` multinivel backward-compatible + `resolve_preparation_costs()`
   recursivo con guard anti-ciclo + prorrateo por rendimiento), excepciones
   `InvalidRecipeComponent`+`RecipeCycle`. 8 unit tests (incl. **paridad**).
2. **Wiring** (`9059f67`) — migración **0021** (`preparations`+`preparation_items` RLS +
   `recipe_items.preparation_id`, `ingredient_id` nullable); ORM/mappers;
   `PreparationRepository`; los 2 consumidores de food cost (`ProjectOrderSales` +
   `SqlAlchemyFoodCostReadModel`) resuelven `cost_by_preparation` (un ciclo NO rompe el
   cobro → degrada a 0); `consume.py` saltea ítems de prep (**stock anidado DIFERIDO**);
   container. e2e de propagación al proyectar.
3. **CRUD** (`0ff5bcd`) — use cases `ListPreparations`/`SavePreparation`(guard anti-ciclo al
   guardar)/`DeletePreparation`; `SetRecipe` acepta preparaciones; schema XOR; endpoints
   `/inventory/preparations` GET/POST/PUT/DELETE; errores mapeados (404/422/409). e2e de
   propagación vía API (sube costo insumo → sube food cost 150→300), ciclo 409, XOR, aislamiento.
4. **Frontend** (`ad6789a`) — types/api/hooks; `recipe-items.ts` (helpers puros);
   `preparations-manager.tsx` (sección "Recetas madre" + `ComponentRowsEditor` reutilizable);
   el editor de receta del producto usa insumos y/o preparaciones.

## Validación
| Check | Estado |
|---|---|
| Backend pytest | ✅ 399 (foundation 8 unit + wiring 1 e2e + CRUD 5 e2e) |
| Backend ruff | ✅ (archivos tocados) |
| Migración 0021 → dev | ✅ |
| Front build / tests / lint | ✅ 137 tests |
| **Paridad** (receta plana = igual que antes) | ✅ (unit + full suite sin regresión) |

## Diferido / notas
- **Consumo de stock de preparaciones anidadas**: vender un plato con una preparación
  NO descuenta los insumos de la prep del stock (el food cost sí es exacto). Documentado;
  follow-up si se pide.
- **"Usada en N platos"** en la UI: diferido (necesitaría un endpoint de conteo o traer
  todas las recetas).
- E501 pre-existentes en `finance_snapshot_repo.py` (no míos).
- Quedó un reorder de imports trivial sin commitear en `me.py` (no es de esta tanda).

## Estado del plan
Productos v2 **A + B + C completas** → plan archivado a `completed/`.
