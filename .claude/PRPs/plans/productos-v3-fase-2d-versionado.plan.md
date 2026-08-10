# Plan: Productos v3 — Fase 2, Tanda 2D (Versionado de recetas + costo de reposición)

## Summary

Última tanda "de motor" de la Fase 2 (2A merma / 2B IVA / 2C conversión ya en `main`). A diferencia de 2A/2B/2C, **2D casi no toca `domain/inventory/costing.py`**: la exploración confirma que las dos capacidades que el nombre implica **ya están mayormente resueltas** por infraestructura existente. 2D es la tanda de **metadata + read models**, no de matemática de costo.

Las dos capacidades y su estado real:

1. **Costo de reposición ("último precio") — YA ES EL DEFAULT.** `Ingredient.set_cost` (`entities.py:85-91`) aplica política de *último costo* en cada `RegisterPurchase` (`use_cases.py:191`), así que `Ingredient.unit_cost` **ya es** el precio de la última compra = costo de reposición. El PRD lo dice literal (línea 147: *"costo de reposición (último precio, ya default)"*). El **histórico de costo de insumo** tampoco necesita tabla nueva: `stock_movements` ya congela `unit_cost_amount`/`unit_cost_currency` por compra (`models.py:555-556`) y ya existe `list_for_ingredient` (`stock_movement_repo.py:66`). Delta real de T1.4: **cero cambios de motor** + un read model fino sobre `stock_movements`.

2. **Versionado de receta — LARGAMENTE INNECESARIO para exactitud histórica.** `projection.py:147-148` **ya congela** `food_cost_amount` **y** `food_cost_net_amount` por línea en `sale_facts` al pagar. El food cost histórico por venta **ya está congelado punto-en-el-tiempo**. Lo único que el versionado agrega es **atribución/auditoría** (poder decir "el costo del plato subió porque cambiaste la receta el 12/03" vs "porque subió el bife"), no exactitud. Delta real de T1.6: un `version:int` incremental en la receta + snapshot `recipe_version` en `sale_facts`. Aditivo, paridad total.

**Recomendación honesta: 2D está ~80% cubierto. No fabricar feature.** El delta mínimo coherente es: (a) confirmar/testear que reposición = último costo (sin código de motor); (b) exponer histórico de insumo desde `stock_movements` (read model, sin migración); (c) `Recipe.version` + `sale_facts.recipe_version` (migración **0027**, aditiva). `costing.py` queda **byte por byte igual** — la paridad es por construcción, más fuerte que en 2A/2B/2C.

## What the PRD asks vs defers (quoted)

No hay un ticket "2D" discreto: 2A–2D es la descomposición que el equipo hizo de la Fase 2. Con 2A/2B/2C hechos, **2D = los tickets restantes de Fase 2: T1.4, T1.5, T1.6.**

**Lo que pide (citado):**
- Fila Fase 2 (línea 128): *"...costo de reposición + histórico de insumo (T1.4), tope de profundidad (T1.5), versionado de receta + snapshot (T1.6)"*.
- Phase Details (línea 147): *"...costo de reposición (último precio, **ya default**) + histórico de costo de insumo; tope de profundidad 5 + ciclos (**ya ✅**); recipe_version + snapshot al vender."*
- MoSCoW (línea 78): *"Should | Versionado de receta + snapshot histórico correcto (T1.6) | Sin esto el histórico es ficción"*.
- Arquitectura (línea 107): *"Snapshot por venta ya existe: sale_facts congela food_cost al pagar (ProjectOrderSales). **Falta recipe_version para el histórico correcto** (T1.6)."*
- Riesgo (línea 119): *"Versionado de receta agranda el modelo | M | **recipe_version incremental + snapshot ya existente en sale_facts**"*.
- Decisions Log (línea 202): *"Costo a usar | Último precio (reposición), configurable | Promedio ponderado | En inflación, el promedio subestima reponer"*.

**Lo que difiere / NO pide en v1:**
- El **display** del histórico (gráfico de costo del plato, alertas "el bife subió 12%", receta-como-estaba) es **Fase 7 (Ficha completa)**, no 2D. 2D deja el dato disponible; la UI de ficha es otra fase.
- **Costeo configurable promedio-ponderado**: el PRD lo nombra "configurable" pero fija último-precio como default y "ya default". Construir el método alternativo es gold-plating → **diferido**.
- **Snapshot item-level de la receta** (guardar los ingredientes/qty tal cual estaban en cada venta): innecesario — `sale_facts` ya congela el **número** de costo; el `version:int` alcanza para atribuir/detectar cambios. **Diferido.**
- **Tope de profundidad 5 (T1.5)**: los ciclos **ya están guardados** (`RecipeCycle`, `costing.py:109-110`). Un cap de profundidad explícito es defensivo y trivial; se incluye como sub-tarea opcional o se difiere.

## Design decision (recommended + alternatives + deferred)

### ✅ Recomendado — metadata aditiva, `costing.py` intacto

**T1.6 (versionado):**
- `Recipe.version: int = 1` en el dominio (`recipe.py`). `SetRecipe` lee la receta actual (ya tiene el repo) y guarda `version = old+1` (o 1 si es nueva). El repo `save` (que hoy hace `merge` + delete-all-items + re-add, `recipe_repo.py:81-91`) persiste el `version`.
- Snapshot: `projection.py` lee `recipe.version` y lo escribe en `sale_facts.recipe_version` (nueva columna nullable). `SaleFact` (`facts.py`) gana `recipe_version: int | None = None`.
- Migración **0027**: `recipes.version` (`server_default="1"`, backfilla recetas viejas a v1) + `sale_facts.recipe_version` (nullable → filas previas = "sin versión").

**T1.4 (reposición + histórico):**
- **Reposición**: sin cambio de código. Último-costo ya es el default. Se agrega **un test que lo fija** (una segunda compra a mayor precio actualiza `unit_cost` y el food cost sube) + una línea UX en español en la ficha ("Costo a precio de reposición: última compra").
- **Histórico de insumo**: read model fino `IngredientCostHistoryReadModel` sobre `stock_movements` (reason=PURCHASE, `unit_cost_amount` por `created_at`), reutilizando el `list_for_ingredient` existente o un select dedicado tenant-scoped. **Sin migración, sin tabla.**

**Por qué esta**: (a) `food_cost()`/`resolve_preparation_costs()` **no se tocan** → paridad por construcción (la más fuerte de las cuatro tandas); (b) el snapshot de costo ya existe, sólo se le agrega la etiqueta de versión; (c) el dato de reposición e histórico **ya está**, no se duplica; (d) impacto DI mínimo.

### Alternativas
- **A — Tabla `recipe_versions` con snapshot item-level** (ingredientes+qty por versión). Da "ver la receta como estaba". Contra: tabla nueva + escritura por cada `SetRecipe` + no aporta exactitud (el costo ya está congelado en `sale_facts`). **Diferida a Fase 7** si el dueño pide ver recetas viejas.
- **B — Costeo configurable (promedio ponderado vs último)**. Agrega `costing_method` en settings + rama en el read model. Contra: el PRD ya elige último-precio; es el alternativo del Decisions Log, no el v1. **Diferida.**
- **C — Recalcular histórico desde recetas versionadas en cada lectura** (no snapshot). Contra: contradice el patrón `sale_facts` (silver congelado) y reintroduce "histórico ficción" al cambiar recetas. **Descartada.**

### Deferred (explícito)
- Snapshot item-level de receta (Alt. A) → Fase 7.
- Método de costeo configurable (Alt. B).
- Alertas "el bife subió X%" y gráfico de costo del plato → Fase 7 (consumen el histórico que 2D deja disponible).
- Tope de profundidad 5 (T1.5): incluir como constante defensiva `MAX_RECIPE_DEPTH=5` en `resolve_preparation_costs` **o** diferir (ciclos ya guardados). Recomendado: incluir, es 3 líneas y no cambia números.

### Resolución explícita de las dos preguntas clave
- **¿Hace falta versionado dado que `sale_facts` ya congela el costo?** No para exactitud — `projection.py:147-148` ya congela bruto y neto por línea. El versionado sólo compra **atribución** (distinguir cambio-de-receta de cambio-de-precio-de-insumo) y **auditoría**. Por eso el delta es un `int` + snapshot, no un modelo grande.
- **¿Reposición reusa la infra de inflación 2B?** No. La infra 2B (`advisor_settings.monthly_inflation_bps`, `product_price_changes`, migración 0020) es **precio de venta vs inflación** (Fase 5), otro dominio. El costo de reposición es simplemente el **último costo** (`Ingredient.set_cost`, ya default) y su histórico ya vive en `stock_movements`. **Ni la infra 2B ni una tabla nueva de compras son necesarias.**

## Patterns to Mirror (file:line)

- **Campo nuevo aditivo con default (paridad)** — `entities.py:64` (`yield_pct`), `:67` (`cost_includes_tax`), `:70` (`recipe_unit`). `Recipe.version` sigue el mismo criterio (default, sin `__post_init__` que valide filas viejas).
- **Migración add-column con server_default** — `0026_recipe_unit.py` (header `revision`/`down_revision`), y `0022_ingredient_yield.py` para `server_default`. 0027: `recipes.version` con `server_default="1"`, `sale_facts.recipe_version` nullable.
- **Snapshot en la proyección** — `projection.py:127-171` (loop que arma `SaleFact` y congela `food_cost_amount`/`food_cost_net_amount`). Agregar `recipe_version=recipe.version if recipe else None`.
- **Read model tenant-scoped de sólo lectura** — `finance_repo.py:81-133` (`SqlAlchemyFinanceProductDetailReadModel`) y `product_pricing_repo.py:61-81` (`list_for_product`) para el patrón de historial ascendente por `changed_at`. El de insumo lo replica sobre `stock_movements`.
- **Repo que reemplaza el set completo** — `recipe_repo.py:81-91` (`save`: merge + delete items + re-add). Persiste el `version` en el `RecipeORM` mergeado.
- **Use case Create/Update con lectura previa** — `use_cases.py:296-312` (`SetRecipe`): agregar un `get_for_product` para leer el `version` actual antes de guardar.
- **Puerto read model + DTO** — `finance/use_cases.py` (ABC `FinanceProductDetailReadModel`) + `finance/dtos.py` (`ProductDetail`, `ProductSaleLine`) como molde del `IngredientCostHistory` DTO/puerto.
- **Tests de paridad + snapshot** — `tests/unit/test_effective_unit_cost.py` (estructura de paridad); `tests/integration/test_e2e_food_cost.py` y de proyección/`sale_facts` para el snapshot de versión.

## Files to Change (por capa)

### Domain (backend)
- **MODIFY** `backend/app/domain/inventory/recipe.py` — `Recipe.version: int = 1`.
- **MODIFY** `backend/app/domain/inventory/value_objects.py` — *(opcional T1.5)* `MAX_RECIPE_DEPTH = 5`.
- **MODIFY** `backend/app/domain/inventory/costing.py` — *(sólo si se incluye T1.5)* pasar un contador de profundidad en `resolve_preparation_costs` que corte a 5. **La matemática de línea NO cambia.** Si se difiere T1.5, este archivo queda intacto.
- *(opcional)* **CREATE** `backend/app/domain/inventory/cost_history.py` **o** DTO en application — dataclass `IngredientCostPoint(occurred_at, unit_cost_amount, currency)`.

### Persistence (backend)
- **CREATE** `backend/alembic/versions/0027_recipe_version.py` — `op.add_column("recipes", sa.Column("version", sa.Integer(), server_default="1", nullable=False))` + `op.add_column("sale_facts", sa.Column("recipe_version", sa.Integer(), nullable=True))`; `down_revision="0026_recipe_unit"`; `revision="0027_recipe_version"` (17 ≤ 32, debe coincidir con el filename).
- **MODIFY** `backend/app/infrastructure/persistence/models.py` — `RecipeORM.version: Mapped[int]` (`server_default="1"`, `:474`); `SaleFactORM.recipe_version: Mapped[int | None]` (nullable, `:613`).
- **MODIFY** `backend/app/infrastructure/persistence/mappers.py` — mapear `version` en `recipe_to_domain`/`recipe_to_orm` y `recipe_version` en el mapper de `SaleFact`.
- **MODIFY** `backend/app/infrastructure/persistence/recipe_repo.py` — `get_for_product`/`list_for_products` devuelven `version`; `save` persiste `version` (mismo `merge`).
- **CREATE/MODIFY** read model de histórico de insumo — nuevo `SqlAlchemyIngredientCostHistoryReadModel` (select PURCHASE sobre `StockMovementORM` tenant-scoped, `unit_cost_amount` asc por `created_at`) **o** reusar `SqlAlchemyStockMovementRepository.list_for_ingredient` filtrando PURCHASE en un use case.

### Application (backend)
- **MODIFY** `backend/app/application/analytics/facts.py` — `SaleFact.recipe_version: int | None = None`.
- **MODIFY** `backend/app/application/analytics/projection.py` — en el loop (`:128-170`) setear `recipe_version=recipe.version if recipe is not None else None`. **No toca el cálculo de food cost.**
- **MODIFY** `backend/app/application/inventory/use_cases.py` — `SetRecipe.execute`: leer receta actual (`get_for_product`), `new_version = (current.version + 1) if current else 1`, construir `Recipe(..., version=new_version)`.
- *(opcional)* **CREATE** `GetIngredientCostHistory` use case + puerto ABC en `application/inventory/` (o `finance/`) para el histórico de insumo.

### Presentation (backend)
- *(opcional, thin)* **MODIFY** `schemas/inventory.py` + `api/v1/inventory.py` — exponer `version` en la respuesta de `GET /.../recipe` y/o endpoint `GET /inventory/ingredients/{id}/cost-history`. Puede diferirse a Fase 7 si el front aún no lo consume.

### DI
- **MODIFY** `backend/app/container.py` — `set_recipe` (`:879`) y `project_order_sales` (`:572`) **no cambian de firma** (ya inyectan `recipe_repository`). Si se agrega el read model de histórico: nuevo provider + wire en el use case de ficha. `advisor_settings_repository` ya está definido antes de `project_order_sales` (`:568-569`), sin reordenamientos.

### Frontend
- *(mínimo en 2D; grueso en Fase 7)* `frontend/src/api/types-inventory.ts` — `recipe.version?` en el DTO de receta; tipo `IngredientCostPoint` si se expone el endpoint. Línea UX en español en la ficha: *"Costo a precio de reposición (última compra)."* El gráfico/alertas de histórico son Fase 7.

## Step-by-Step Tasks (ordenadas)

1. **Dominio: `Recipe.version`** — `recipe.py` add `version: int = 1`. *Mirror*: `yield_pct` en `entities.py`. *Gotcha*: sin `__post_init__` que valide; default 1.
2. **Migración 0027** — `recipes.version` (`server_default="1"`, non-null, backfilla viejas a 1) + `sale_facts.recipe_version` (nullable). *Mirror*: `0026_recipe_unit.py`. *Gotcha*: `revision` == filename (F12 del review de 2B); `down_revision="0026_recipe_unit"`; nullable en `sale_facts` = filas previas "sin versión".
3. **ORM + mappers + repo** — `RecipeORM.version`, `SaleFactORM.recipe_version`; mapear en ambos mappers; `recipe_repo.save` persiste `version`, `get`/`list_for_products` lo devuelven. *Gotcha*: `merge(recipe_to_orm(recipe))` ya arrastra el `version` seteado.
4. **`SetRecipe` incrementa versión** — leer `get_for_product` antes de guardar; `version = old+1` o 1. *Mirror*: patrón "leer antes de escribir" de use cases. *Gotcha*: receta nueva → v1; el `save` sigue reemplazando items (sin cambio).
5. **Snapshot en proyección** — `facts.py` add `recipe_version`; `projection.py` setea `recipe.version` en cada `SaleFact`. *Gotcha*: producto sin receta → `None`; **no tocar** el cálculo de `food_cost_amount`/`net`.
6. **Reposición: test + UX** — test que fija último-costo como reposición (2ª compra mayor → `unit_cost` y food cost suben). Línea UX en la ficha. *Gotcha*: **cero código de motor**; es confirmación explícita.
7. **Histórico de insumo (read model)** — select PURCHASE tenant-scoped sobre `stock_movements` (`unit_cost_amount` asc por `created_at`), o reusar `list_for_ingredient`. *Mirror*: `list_for_product` en `product_pricing_repo.py`. *Gotcha*: filtrar `reason=PURCHASE` y `unit_cost_amount IS NOT NULL`; sin migración.
8. *(opcional T1.5)* **Tope de profundidad 5** — contador en `resolve_preparation_costs`. *Gotcha*: no cambia números (sólo corta anidamientos >5, ya raros); si complica la paridad, diferir.
9. **Tests + validación** (abajo).

## Testing Strategy (incl. paridad)

**Test de paridad (default byte-for-byte igual):**
- Suite completa verde **sin cambios de números**. Como `costing.py` no se toca (o sólo se agrega un cap que no afecta anidamientos ≤5), la paridad de food cost/margen/Finanzas es por construcción.
- `sale_facts.recipe_version` NULL en filas previas no altera ningún agregado (`finance_repo`/`kpis` no lo leen).

**Tests nuevos (`asyncio_mode=auto`, sin marker):**
- unit: `SetRecipe` sobre receta v1 → v2; receta nueva → v1.
- integration: venta paga de un plato con receta v2 → `sale_facts.recipe_version == 2`; producto sin receta → `None`; `food_cost_amount` idéntico al de hoy (snapshot no altera el número).
- integration: 2ª compra de un insumo a mayor precio → `unit_cost` = último costo y el food cost del plato sube (reposición = último precio).
- unit/integration: histórico de insumo devuelve las compras ascendentes con su `unit_cost_amount`; tenant-scoped (no filtra otro tenant).
- *(si T1.5)* preparación anidada >5 niveles → corte controlado (sin crash), anidamiento ≤5 idéntico a hoy.

## Validation Commands (venv poetry)
```bash
/Users/marce/Library/Caches/pypoetry/virtualenvs/bravo-backend-xQklV81L-py3.12/bin/alembic upgrade head
/Users/marce/Library/Caches/pypoetry/virtualenvs/bravo-backend-xQklV81L-py3.12/bin/ruff check --fix app tests
/Users/marce/Library/Caches/pypoetry/virtualenvs/bravo-backend-xQklV81L-py3.12/bin/python -m pytest   # suite completa = test de paridad

# Frontend (si se toca)
cd /Users/marce/Desktop/BRAVO/frontend && npm run build && npm run lint && npm test
```
Backend 100% inglés (código+comentarios); UX en español; toda query filtra `tenant_id` (+ RLS) — las lecturas nuevas reusan selects tenant-scoped. Cobertura dominio/use-case ≥80%.

## Acceptance Criteria
- [ ] `Recipe.version` (default 1) incrementa en cada `SetRecipe`; se persiste y se lee.
- [ ] Migración **0027** aplicada: `recipes.version` (server_default 1, recetas viejas = v1) + `sale_facts.recipe_version` (nullable). `revision` == filename.
- [ ] `sale_facts.recipe_version` se congela al pagar; producto sin receta → `None`; `food_cost_amount`/`food_cost_net_amount` **idénticos** a hoy.
- [ ] `costing.py` sin cambios de matemática; suite completa verde sin cambios de números (paridad Finanzas).
- [ ] Reposición = último precio confirmado por test (2ª compra sube el food cost); histórico de costo de insumo disponible desde `stock_movements` (read model tenant-scoped), **sin tabla nueva**.
- [ ] DI: `SetRecipe`/`project_order_sales` sin cambio de firma; providers nuevos (si el read model se expone) wired.

## Risks & Rollback
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Snapshot de versión altera números de Finanzas | Muy baja | Alto | Es metadata; `costing.py` intacto; `recipe_version` no lo lee ningún agregado; test de paridad |
| `SetRecipe` no incrementa (o pisa a 1) | Media | Medio | Leer `get_for_product` antes; test v1→v2 y nueva→v1 |
| Migración 0027 con non-null sin default rompe recetas viejas | Baja | Alto | `server_default="1"` backfilla; `sale_facts.recipe_version` nullable |
| Fabricar scope (tabla de versiones item-level, costeo configurable) | Media | Medio | Explícitamente diferido; 2D = `int` + snapshot + read model fino |
| Histórico de insumo re-implementa lo que ya está | Media | Bajo | Reusar `stock_movements`/`list_for_ingredient`; no tabla nueva |

**Rollback**: `alembic downgrade -1` (drop `recipes.version` + `sale_facts.recipe_version`); revertir código. Todo lo nuevo es aditivo/identidad → sin dato en riesgo (recetas viejas = v1, sale_facts previos = versión NULL).

## Notes
- **Por qué 2D casi no toca `costing.py`** (a diferencia de 2A/2B/2C): 2A/2B/2C extendían la **matemática** (merma, IVA, conversión) con parámetros identidad. 2D es **metadata + read models** sobre datos ya congelados (`sale_facts`) y ya capturados (`stock_movements`) — la paridad es aún más fuerte porque el motor no se toca.
- El **valor real** del versionado no es exactitud (ya la da `sale_facts`) sino **atribución** en la Ficha (Fase 7): distinguir "cambió la receta" de "subió el insumo". 2D deja la etiqueta; Fase 7 la usa.

### Critical Files for Implementation
- backend/app/application/analytics/projection.py
- backend/app/application/inventory/use_cases.py
- backend/app/infrastructure/persistence/recipe_repo.py
- backend/app/infrastructure/persistence/models.py
- backend/app/domain/inventory/recipe.py
