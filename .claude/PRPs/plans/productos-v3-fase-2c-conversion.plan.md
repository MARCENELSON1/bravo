# Plan: Productos v3 — Fase 2, Tanda 2C (Conversión de unidades)

## Summary
Permitir que un insumo se **compre/costee en su unidad grande** (`Ingredient.unit`: KG o L) pero se **use en receta en la sub-unidad de la misma familia** (G o ML), sin perder exactitud ni romper el motor de food cost. Se agrega un campo opcional `Ingredient.recipe_unit` (misma familia que `unit`, más fino; `None` = paridad total). La cantidad de receta pasa a estar en milésimas de `recipe_unit`; el factor de conversión (siempre 1000 dentro de familia, entero, determinístico) entra en el **único redondeo de la línea de costo** como parámetro opcional identidad, y en el descuento de stock de `consume.py`. Con `recipe_unit = None` el motor se reduce exactamente al de hoy → **paridad garantizada, cero cambio en Finanzas**. Migración **0026** (add column nullable). Cuarta y última tanda "de motor" de la Fase 2.

> El spec NO pide g↔ml (necesita densidad) ni "cajas de 24" (no hay unidad CASE en el enum). Se acota deliberadamente a las familias que el enum ya expresa: **masa (KG↔G) y volumen (L↔ML)**, factor fijo 1000.

## User Story
Como **dueño (OWNER/MANAGER)**, quiero **cargar el aceite por litro y usarlo en ml en la receta** (y la harina por kg / en g), para que **el food cost salga correcto sin tener que tipear "0,01 l" ni perder precisión con cantidades chicas**.

## Problem → Solution
Hoy `RecipeItem.qty` está en milésimas de **la unidad base del insumo**, que es también la de compra/stock (docstring de `UnitOfMeasure`: *"stock, recipe and purchase all share the ingredient's own base unit"*). Si comprás por litro, tenés que expresar 10 ml como `qty=10` (= 0,01 L) y una pizca de un insumo caro por kg literalmente **redondea a 0** en milésimas de kg. Solución: declarar por insumo una `recipe_unit` más fina; la receta se tipea/almacena en esa unidad; el costo sigue guardado por unidad de compra (exacto) y el factor 1000 entra en el cálculo de la línea en un solo redondeo.

## Metadata
- **Complexity**: Medium (~13 archivos; back + front). Toca el núcleo del costeo, pero de forma estrictamente aditiva/identidad.
- **Source PRD**: `.claude/PRPs/prds/productos-v3.prd.md` — Fase 2, Ticket **T1.1** (líneas 128, 147; troceo 2A línea 27).
- **PRD Phase**: 2 (Tanda 2C de 4). Depende conceptualmente de 2A/2B (ya en `main`).
- **Migración**: **0026** (`0026_recipe_unit`, 16 chars ≤ 32; add column `ingredients.recipe_unit` NULLABLE).

### Qué pide el spec y qué difiere (citado del PRD)
- Fase 2 scope (línea 147): *"tabla de conversión de unidades por familia (no g↔ml sin densidad)"*.
- Troceo 2A (línea 27): *"2C — Conversión de unidades | Tabla de conversión por familia (kg↔g, L↔ml)"*.
- **Difiere**: g↔ml (densidad), packs/cajas arbitrarios (no hay unidad CASE), y unidades editables por tenant. El "factor por familia" es una constante física (1000), no un dato de usuario → **no se crea tabla en DB**.

---

## Cómo se interpreta HOY una cantidad de receta (verificado en código)
- `value_objects.py:8` `QUANTITY_SCALE = 1000`. `RecipeItem.qty` (`recipe.py:10-12`) está en **milésimas de la unidad base del componente**.
- `costing.py:72` (food_cost) y `costing.py:110` (resolve_preparation_costs): la línea es `round(cost.amount * item.qty / QUANTITY_SCALE)`, con `cost` = Money por **una** unidad base del insumo (o de la preparación). O sea `costo_unidad_base × cantidad_en_unidades_base`.
- `cost_by_ingredient` se construye en **dos** lugares (los "bordes" que 2A/2B ya usaron):
  - `food_cost_repo.py:93-100` (desde columnas ORM, con `effective_unit_cost`/`net_effective_unit_cost`).
  - `projection.py:88-91` (desde dominio, `ing.effective_unit_cost`).
- Stock: `consume.py:69` descuenta `item.quantity * recipe_item.qty` directo del `stock_qty` (milésimas de unidad base). **Este es el único consumidor de `qty` fuera del costeo.**

**Dónde entra el factor sin romper el motor**: la conversión escala la **cantidad**, no el costo. Matemáticamente `costo × qty` es simétrico, así que el factor puede plegarse en la línea de costo. Para no perder precisión (dividir el costo por 1000 rompe insumos baratos usados en poca cantidad; ej. ARS 15,50/kg × 300 g daría ARS 6,00 en vez de ARS 4,65), el factor entra en el **único redondeo de la línea** manteniendo el costo por unidad de compra (exacto). Con factor identidad, la fórmula es idéntica a la de hoy → paridad exacta.

---

## Design decision (recommended + alternatives + deferred)

### ✅ Recomendado — `Ingredient.recipe_unit` opcional + factor entero identidad en la línea
1. **Modelo**: `Ingredient.recipe_unit: UnitOfMeasure | None = None`. `unit` sigue siendo la unidad de **compra/costo/stock** (KG o L). `recipe_unit` sólo puede ser la **sub-unidad más fina de la misma familia** (KG→G, L→ML) o `None`. `None` ⇒ receta en la unidad base (comportamiento actual).
2. **Almacenamiento de receta**: `RecipeItem.qty` pasa a estar en milésimas de `recipe_unit` cuando está seteada (si `None`, sin cambio: milésimas de `unit`).
3. **Costeo (paridad exacta)**: `cost_by_ingredient` **sigue guardando el costo por unidad de compra** (`unit`), exacto. Se pasa a `food_cost()`/`resolve_preparation_costs()` un `factor_by_ingredient` **opcional** (`dict[str, tuple[int,int]]`, num/den; ausente = `(1,1)`). La línea:
   ```
   total += round(cost.amount * item.qty * num / (den * QUANTITY_SCALE))
   ```
   Con `(num,den)=(1,1)` esto es **carácter por carácter** el `round(cost.amount * item.qty / QUANTITY_SCALE)` actual → paridad. Para KG→G: `1 g = 1/1000 kg` ⇒ `(num,den)=(1,1000)`; ej. ARS 15,50/kg (1550) × 300 g (300000 milésimas) → `1550*300000*1/(1000*1000)=465` c **exacto**; una pizca 0,5 g de un insumo a 5000/kg → `500000*500/1000000=250` c **exacto**.
4. **Stock**: en `consume.py` se convierte `recipe_qty → base_qty` con el mismo factor (`round(item.quantity * recipe_item.qty * num / den)`) antes del OUT. `None` ⇒ sin cambio.
5. **Factor**: helper puro en dominio (`recipe_conversion.py` o en `value_objects.py`) con un mapa cerrado de familia `{KG:(G,1000), L:(ML,1000)}` y una función `conversion_factor(base, recipe) -> tuple[int,int]` + validación `assert_convertible(base, recipe)`.

**Por qué esta**: (a) mantiene el costo almacenado **exacto** (por unidad de compra, que es lo que el dueño conoce); (b) el cambio a `food_cost`/`resolve` es **puramente aditivo e identidad** (parámetro opcional con default), así que la paridad es por construcción, igual criterio que 2A/2B; (c) resuelve el problema real (precisión en cantidades chicas) que un enfoque "solo UI" no resuelve (milésimas de kg no representan 0,5 g); (d) **no toca el DI container** (todos los consumidores ya tienen el repo de ingredientes).

### Alternativa A — Factor plegado en el dict (borde puro, sin tocar `food_cost`)
Guardar `cost_by_ingredient` como **costo por `recipe_unit`** (`round(costo_base/1000)`) y no tocar `food_cost()`. Más fiel al "no tocar el motor" de 2A, **cero cambios en costing.py**. Contra: pierde precisión de costo en insumos baratos (ej. ARS 15,50/kg → 2 c/g, error acotado ~ARS 1,35 por línea; en agregado queda dentro del ±2% del margen, pero no es exacto). **Recomendada como fallback** si el equipo prefiere cero cambios en `costing.py`.

### Alternativa B — Conversión del lado de la compra (`purchase_unit`)
Hacer que `unit` sea la unidad **fina** (g/ml) y agregar `purchase_unit` (kg/L) usado sólo para cargar el precio (`cost_per_g = price_per_kg/1000` al comprar). Ventaja: **cero cambios** en costing/stock/consume. Contra: degrada la precisión del costo **almacenado** de forma permanente; cambia stock/min a la unidad fina (números grandes); cambia la semántica de `unit` de todos los insumos. Descartada por invasiva en stock.

### Alternativa C — Unidad + factor por ítem de receta (`recipe_items.unit`/`factor`)
Máxima flexibilidad (mismo insumo en g en una receta y kg en otra). Contra: agrega columnas a `recipe_items` **y** `preparation_items`, factor denormalizado por línea, más UI. Sobredimensionado para el spec. **Diferida.**

### Sub-decisiones a diferir
- **Cambiar `recipe_unit` en un insumo ya usado en recetas**: sus `qty` existentes quedarían reinterpretados por 1000. Regla v1 recomendada: `recipe_unit` **sólo se setea al crear** o cuando el insumo **no está en ninguna receta/preparación**; si se permite cambiarla, hay que **rescalar en la misma transacción** los `recipe_items`/`preparation_items` que lo referencian. Diferir el rescale automático; en v1 bloquear el cambio si está en uso (mensaje UX en español). **Al rollout todos son `None` ⇒ recetas actuales intactas.**
- Familias adicionales / g↔ml con densidad / packs: futuro (T futuro).
- Precisión sub-milésima del **stock** en consumos chicos (pizca): stock está fuera de alcance del PRD; se documenta como limitación conocida.

---

## Patterns to Mirror (file:line)

- **Extensión aditiva del motor con default identidad** — `costing.py:31-40` `net_effective_unit_cost` (parámetro extra, identidad cuando VAT=0). Copiar ese criterio: `food_cost(..., factor_by_ingredient=None)` con default `(1,1)`.
- **Idioma entero/round del motor** — `costing.py:72,110` `round(cost.amount * item.qty / QUANTITY_SCALE)`. La nueva línea agrega `* num / (den * QUANTITY_SCALE)` en el **mismo** `round`.
- **Los DOS bordes del cost dict** — `food_cost_repo.py:82-100` y `projection.py:86-91`. Ambos deben aportar el `factor_by_ingredient` (mismo criterio que 2A: si tocás uno solo, drill-down y snapshot divergen).
- **Campo nullable nuevo en `Ingredient`** — `entities.py:64` (`yield_pct`), `:67` (`cost_includes_tax`). Agregar `recipe_unit` con default, sin `__post_init__` (para no validar filas viejas).
- **Migración add-column** — `alembic/versions/0025_food_cost_net.py:24-27` (header `revision`/`down_revision`), y el patrón `op.add_column` de 0022/0025. `recipe_unit` **nullable** (NULL = paridad, sin `server_default`).
- **ORM + mapper del insumo** — `models.py:423-444` (`IngredientORM`, ver `yield_pct:438`), `mappers.py:590-619` (`ingredient_to_domain`/`_to_orm`, ver `yield_pct`).
- **Use case Create/Update con campo opcional** — `use_cases.py:53-85` (`CreateIngredient`), `:109-137` (`UpdateIngredient`, patrón "si viene, setear").
- **Schemas request/response** — `schemas/inventory.py:11-42` (`CreateIngredientRequest`/`UpdateIngredientRequest`/`IngredientResponse`, ver `yield_pct`/`cost_includes_tax`).
- **Router** — `inventory.py:108-123` (create), `:141-156` (update): pasar el campo.
- **Front tipos + helpers** — `types-inventory.ts:7-37` (`IngredientDTO`/bodies), `lib/inventory.ts:14-32` (`UNIT_OPTIONS`, `formatQty`, `toMilesimas`), `recipe-items.ts:13-28` (`itemsToDrafts`/`draftsToItems`, hoy divide por 1000 fijo).
- **Front form insumo** — `stock-page.tsx:57-108` (`CreateIngredientSheet`, ver `yield`/`inclVat`), `:351-415` (`EditIngredientForm`).
- **Front editor de receta** — `product-catalog.tsx:109-129` (`RecipeEditor`/`RecipeForm`), usa `recipe-items.ts` para qty↔milésimas.
- **Tests de paridad + conversión** — `tests/unit/test_effective_unit_cost.py` (estructura de paridad); `tests/integration/test_e2e_preparations_api.py` (propagación de costo); `tests/integration/test_e2e_food_cost.py`.

---

## Files to Change

### Domain (backend)
- **CREATE** `backend/app/domain/inventory/recipe_conversion.py` — mapa de familia `{KG:(G,1000), L:(ML,1000)}`, `conversion_factor(base, recipe) -> tuple[int,int]`, `assert_convertible(base, recipe)`. (Alternativa: colocar en `value_objects.py` junto a `QUANTITY_SCALE`.)
- **MODIFY** `backend/app/domain/inventory/entities.py` — `Ingredient.recipe_unit: UnitOfMeasure | None = None`.
- **MODIFY** `backend/app/domain/inventory/costing.py` — `food_cost()` y `resolve_preparation_costs()`: parámetro opcional `factor_by_ingredient: dict[str, tuple[int,int]] | None = None`, aplicar `* num / (den * QUANTITY_SCALE)` en la línea (default identidad).
- **MODIFY** `backend/app/domain/inventory/exceptions.py` — nueva `IncompatibleUnits` (código `incompatible_units`, mensaje UX en español).

### Persistence (backend)
- **CREATE** `backend/alembic/versions/0026_recipe_unit.py` — `op.add_column("ingredients", sa.Column("recipe_unit", sa.String(10), nullable=True))`; `down_revision="0025_food_cost_net"`.
- **MODIFY** `backend/app/infrastructure/persistence/models.py` — `IngredientORM.recipe_unit: Mapped[str | None] = mapped_column(String(10), nullable=True)` (después de `unit`, ~línea 431).
- **MODIFY** `backend/app/infrastructure/persistence/mappers.py` — mapear `recipe_unit` en `ingredient_to_domain` (:590) y `ingredient_to_orm` (:606); `None` ⇔ `None`.
- **MODIFY** `backend/app/infrastructure/persistence/food_cost_repo.py` — traer `IngredientORM.recipe_unit` en el select (:82-92) y construir `factor_by_ingredient`; pasarlo a `compute_food_cost` (:157-168) y a `resolve_preparation_costs` (:134-145).

### Application (backend)
- **MODIFY** `backend/app/application/analytics/projection.py` — construir `factor_by_ingredient` en el loop de ingredientes (:86-91) y pasarlo a `compute_food_cost` (:122-133) y `resolve_preparation_costs` (:97-113).
- **MODIFY** `backend/app/application/inventory/consume.py` — convertir `recipe_qty → base_qty` con el factor antes del OUT (:67-70). Requiere leer `ingredient.recipe_unit`; el insumo ya se carga en el loop (:75) — reordenar o precargar el mapa de unidades.
- **MODIFY** `backend/app/application/inventory/use_cases.py` — `CreateIngredient.execute` (:53-85) y `UpdateIngredient.execute` (:109-137): aceptar `recipe_unit: str | None`; validar con `assert_convertible`; en Update, bloquear cambio si el insumo está en uso (o rescalar — ver sub-decisión diferida).

### Presentation (backend)
- **MODIFY** `backend/app/presentation/schemas/inventory.py` — `CreateIngredientRequest`/`UpdateIngredientRequest`/`IngredientResponse`: `recipe_unit: UnitOfMeasure | None`.
- **MODIFY** `backend/app/presentation/api/v1/inventory.py` — pasar `recipe_unit` en create (:113-122) y update (:147-155); incluir en `_ingredient_response` (:77-89).

### DI
- `backend/app/container.py` — **sin cambios** (ningún constructor cambia; `consume`, `projection` y `food_cost_repo` ya tienen acceso a los ingredientes). Confirmado en `container.py:572-581, 846, 855-856, 906`.

### Frontend
- **MODIFY** `frontend/src/api/types-inventory.ts` — `IngredientDTO.recipe_unit?`, `CreateIngredientBody.recipe_unit?`, `UpdateIngredientBody.recipe_unit?`, y usar `recipe_unit ?? unit` para escalar en `RecipeItemDTO`.
- **MODIFY** `frontend/src/lib/inventory.ts` — helper `recipeUnitOptions(baseUnit)` (KG→[KG,G], L→[ML,L], resto → solo sí mismo); reusar `UNIT_LABELS`/`toMilesimas`/`formatQty`.
- **MODIFY** `frontend/src/features/products/recipe-items.ts` — `itemsToDrafts`/`draftsToItems` (:13-28) deben escalar por la **`recipe_unit` del insumo** (hoy dividen por 1000 fijo) y etiquetar la unidad correcta.
- **MODIFY** `frontend/src/features/inventory/stock-page.tsx` — `CreateIngredientSheet` (:57) y `EditIngredientForm` (:351): select "Unidad de receta" (opcional, misma familia); en Edit, deshabilitar si el insumo está en uso.
- **MODIFY** `frontend/src/features/products/product-catalog.tsx` — `RecipeForm`/`RecipeEditor` (:109): mostrar/editar la qty en la `recipe_unit` del insumo (label + escala).

### Tests
- **CREATE** `backend/tests/unit/test_recipe_conversion.py` — factor, `assert_convertible`, paridad e identidad de `food_cost`/`resolve` con factor default vs `(1,1000)`.
- **MODIFY/CREATE** `backend/tests/integration/test_e2e_inventory.py` y `test_e2e_food_cost.py` — insumo con `recipe_unit`, food cost exacto, propagación a preparación, descuento de stock convertido.
- **MODIFY** `frontend/src/api/inventory-api.test.ts` — bodies con `recipe_unit`.

---

## Step-by-Step Tasks (ordenadas)

### Task 1 — Dominio: factor de conversión puro
- **File/What**: CREATE `recipe_conversion.py`: `_FAMILY = {KG:(G,1000), L:(ML,1000)}`; `conversion_factor(base, recipe) -> (num,den)` (recipe==base ⇒ `(1,1)`; base coarse→recipe fine ⇒ `(1,1000)`); `assert_convertible(base, recipe)` (permite `recipe is None`, `recipe==base`, o el par fino válido; si no, `IncompatibleUnits`). Add `IncompatibleUnits` a `exceptions.py`.
- **Mirror**: idioma de `value_objects.py` (constantes) + `exceptions.py:21-35`.
- **Gotcha**: sólo permitir base grande → receta fina (KG→G, L→ML); rechazar G→KG, g↔ml, masa↔volumen, cualquier cosa con UNIT distinto de UNIT.

### Task 2 — Motor de costo: factor identidad
- **File/What**: MODIFY `costing.py`: `food_cost(items, cost_by_ingredient, currency, *, cost_by_preparation=None, factor_by_ingredient=None)`; en la línea (:72) usar `num,den = (factor_by_ingredient or {}).get(item.ingredient_id, (1,1))` y `round(cost.amount * item.qty * num / (den * QUANTITY_SCALE))`. Igual en `resolve_preparation_costs` (:110) para ítems de insumo (los ítems de sub-preparación quedan sin factor: `(1,1)`).
- **Mirror**: `net_effective_unit_cost` (param extra identidad).
- **Gotcha**: `factor_by_ingredient=None` ⇒ `{}` ⇒ `(1,1)` ⇒ **fórmula idéntica** a hoy. NO tocar la firma de `margin`/`ratio`. El factor sólo aplica a ítems con `ingredient_id` (una preparación tiene su propia unidad vía `yield_qty`).

### Task 3 — Migración 0026
- **File/What**: CREATE `0026_recipe_unit.py`, add column `ingredients.recipe_unit String(10) nullable=True`, `down_revision="0025_food_cost_net"`.
- **Mirror**: `0025_food_cost_net.py:24-27`.
- **Gotcha**: **nullable, sin `server_default`** — NULL = paridad; filas viejas quedan sin recipe_unit ⇒ recetas actuales intactas. `revision="0026_recipe_unit"` (16 ≤ 32) debe **coincidir** con el filename (F12 del review de 2B).

### Task 4 — ORM + mappers + dominio Ingredient
- **File/What**: `entities.py` add `recipe_unit: UnitOfMeasure | None = None`; `IngredientORM.recipe_unit` (String(10), nullable); `ingredient_to_domain`/`_to_orm` mapear (`UnitOfMeasure(row.recipe_unit) if row.recipe_unit else None`).
- **Mirror**: `yield_pct` en los tres archivos.
- **Gotcha**: no agregar `__post_init__` a `Ingredient` (validar en use case/schema).

### Task 5 — Los DOS bordes del cost dict + stock
- **File/What**: `food_cost_repo.py`: agregar `IngredientORM.recipe_unit` al select (:82-92), construir `factor_by_ingredient = {id: conversion_factor(unit, recipe_unit)}`, pasarlo a `compute_food_cost` y `resolve_preparation_costs` (bruto y neto). `projection.py`: idem en el loop (:86-91) y en las llamadas (:97-113, :122-133). `consume.py`: aplicar el factor en la agregación de consumo (:67-70).
- **Mirror**: 2A Task 4 ("son dos lugares").
- **Gotcha**: si tocás sólo un builder, drill-down (food_cost_repo) y snapshot (projection→sale_facts) divergen. `consume.py` es el **tercer** consumidor de `qty` — sin la conversión, el descuento de stock queda ×1000. Precargar el mapa de unidades en `consume` o mover el `get_by_id` antes de calcular.

### Task 6 — Use cases + schemas + router
- **File/What**: `CreateIngredient`/`UpdateIngredient` aceptan `recipe_unit`; validar con `assert_convertible(UnitOfMeasure(unit), recipe_unit)`; en Update bloquear cambio si el insumo está en uso (o dejar el rescale como diferido). Schemas: `recipe_unit: UnitOfMeasure | None` en request/response. Router: pasar el campo + `_ingredient_response`.
- **Mirror**: `yield_pct`/`cost_includes_tax` en use_cases (:117-135) y schemas (:18-40).
- **Gotcha**: `UpdateIngredient` hoy es no-destructivo (setea sólo si viene). Cambiar `recipe_unit` sobre recetas cargadas corrompe cantidades — validar "en uso" contra `recipes`/`preparations` (nuevo chequeo) o restringir a alta.

### Task 7 — Frontend tipos + helpers + forms + editor de receta
- **File/What**: tipos con `recipe_unit`; `recipeUnitOptions(baseUnit)` en `lib/inventory.ts`; `recipe-items.ts` escala por `recipe_unit ?? unit` en vez de `/1000` fijo; select "Unidad de receta" en `CreateIngredientSheet`/`EditIngredientForm`; `RecipeForm` muestra/edita qty en la `recipe_unit` del insumo con el label correcto.
- **Mirror**: `stock-page.tsx` campo `yield`/`inclVat`; `recipe-items.ts:13-28`.
- **Gotcha**: `recipe-items.ts` hoy asume una sola escala (`/1000`); ahora la escala depende del insumo elegido en la fila → resolver la unidad por `ingredient_id`. Deshabilitar el select de unidad de receta en Edit si está en uso (coherente con el backend). UX en español: "Unidad de receta (opcional): cargá el costo por kg/l y usá g/ml en la receta."

### Task 8 — Tests + validación (ver secciones siguientes).

---

## Testing Strategy

### Test de paridad (prueba que "sin conversión == hoy")
- **Unit** `test_recipe_conversion.py`:
  - `test_food_cost_identity_without_factor`: `food_cost(items, costs, ARS)` **==** `food_cost(items, costs, ARS, factor_by_ingredient=None)` **==** el valor actual (ej. `RecipeItem("carne", qty=200)`, costo 1000 → `Money(200)`), replicando `test_effective_unit_cost.py:34-38`.
  - `test_resolve_preparation_identity_without_factor`: `resolve_preparation_costs` sin factor == suite actual.
  - **Regla de oro**: correr la **suite completa** con `recipe_unit=None` en todos los fixtures → todo verde sin cambios de números (paridad Finanzas).
- **Unit** conversión:
  - `conversion_factor(KG,G)==(1,1000)`, `(L,ML)==(1,1000)`, `(KG,KG)==(1,1)`.
  - `assert_convertible(KG,G)` ok; `(G,ML)`, `(KG,ML)`, `(UNIT,G)`, `(G,KG)` → `IncompatibleUnits`.
  - Exactitud: costo 1550 c/kg, qty 300 g (300000) → línea 465 (no 600). Pizca: 500000 c/kg, 0,5 g (500) → 250.
- **Integration** (`asyncio_mode=auto`, sin marker):
  - Alta de insumo `unit=L, recipe_unit=ML`; receta con qty en ml; `GET /inventory/food-cost` da el costo exacto.
  - Insumo con `recipe_unit` dentro de una **preparación** → costo de la prep y del plato correctos (propagación, mirror `test_e2e_preparations_api.py`).
  - Venta paga → `consume` descuenta stock convertido a la unidad base (no ×1000).
  - `PATCH recipe_unit` sobre insumo en uso → 4xx (regla v1) o rescale correcto (si se implementa).
- **Frontend**: `inventory-api.test.ts` con `recipe_unit`; `npm test` verde.

### Edge cases
- [x] `recipe_unit=None` → paridad exacta (todos los caminos).
- [x] `recipe_unit==unit` → factor `(1,1)` (paridad).
- [x] Familia inválida (g↔ml, masa↔volumen, UNIT) → `IncompatibleUnits` (422).
- [x] Insumo con `recipe_unit` anidado en preparación → propaga.
- [x] Consumo chico (pizca) → stock puede perder sub-milésima (documentado; stock fuera de alcance).

---

## Validation Commands
```bash
# Backend (venv poetry; asyncio_mode=auto)
/Users/marce/Library/Caches/pypoetry/virtualenvs/bravo-backend-xQklV81L-py3.12/bin/alembic upgrade head
/Users/marce/Library/Caches/pypoetry/virtualenvs/bravo-backend-xQklV81L-py3.12/bin/ruff check --fix app tests
/Users/marce/Library/Caches/pypoetry/virtualenvs/bravo-backend-xQklV81L-py3.12/bin/python -m pytest    # suite completa = test de paridad

# Frontend
cd /Users/marce/Desktop/BRAVO/frontend && npm run build && npm run lint && npm test
```
Cobertura dominio/use-case ≥80%. Backend 100% inglés (código+comentarios); textos UX en español. Toda query filtra `tenant_id` (+ RLS) — las nuevas lecturas reusan los selects tenant-scoped ya existentes.

## Acceptance Criteria
- [ ] `Ingredient.recipe_unit` (nullable, default `None`) + helper de factor de familia (KG↔G, L↔ml) con validación `IncompatibleUnits`.
- [ ] `food_cost()`/`resolve_preparation_costs()` aceptan `factor_by_ingredient` opcional **identidad**; la fórmula con `(1,1)` es idéntica a la actual (suite completa verde, sin cambios de números).
- [ ] Los **dos** bordes (`food_cost_repo`, `projection`) y `consume.py` aplican el factor; costo del plato **exacto** con conversión (ej. aceite por litro usado en ml).
- [ ] Migración 0026 aplicada; recetas existentes intactas (todos `recipe_unit=None`).
- [ ] API + forms permiten setear "Unidad de receta"; el editor de receta tipea/muestra en esa unidad; DI container sin cambios.

## Risks & Rollback
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Cambiar `food_cost()` altera números de Finanzas en prod | Baja | Alto | Parámetro **opcional identidad** (`(1,1)`) + test de paridad + suite completa; `recipe_unit=None` en todo lo existente |
| Tocar sólo un builder → drill-down ≠ snapshot | Media | Medio | Task 5 cambia **ambos** + `consume` explícitamente; e2e cubre los tres caminos |
| `consume.py` sin conversión → stock ×1000 mal | Media | Medio | Test e2e de descuento de stock convertido; `consume` es el 3er consumidor de `qty`, cubierto en Task 5 |
| Cambiar `recipe_unit` en insumo ya en receta → cantidades corruptas | Media | Alto | v1: bloquear cambio si está en uso (o rescalar en la misma transacción); al rollout todos `None` |
| Pérdida de precisión de costo (Alternativa A si se elige) | Baja | Bajo | Recomendado usa factor-en-línea (exacto); error de A acotado y dentro de ±2% del margen |

**Rollback**: `alembic downgrade -1` (drop `recipe_unit`); revertir código. Como todo lo nuevo es identidad con `recipe_unit=None`, no hay dato en riesgo salvo insumos que se hayan convertido (esos requieren revertir manualmente sus recetas si se hizo el rescale). Recomendación: feature efectivamente "off" hasta que un insumo setee `recipe_unit`.

## Notes
- **Por qué se toca el motor (a diferencia de 2A/2B)**: la conversión escala la **cantidad**, no el costo; plegarla en el dict de costos (Alternativa A) pierde precisión en insumos baratos usados en poca cantidad. El factor-en-línea con default identidad preserva la paridad exacta y mantiene el costo almacenado por unidad de compra (exacto, el número que el dueño conoce). Sin `Decimal`/float: enteros + un solo `round(cost*qty*num/(den*SCALE))`.
- **Alcance real del enum**: `UnitOfMeasure = {G,KG,ML,L,UNIT}` ya expresa las dos familias con sub-escala (masa, volumen); 2C sólo conecta KG↔G y L↔ML. "Caja de 24" y g↔ml quedan fuera (no hay unidad CASE; g↔ml necesita densidad) — coherente con el PRD.

### Critical Files for Implementation
- backend/app/domain/inventory/costing.py
- backend/app/infrastructure/persistence/food_cost_repo.py
- backend/app/application/analytics/projection.py
- backend/app/application/inventory/consume.py
- backend/app/domain/inventory/entities.py
