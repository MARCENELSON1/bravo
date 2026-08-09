# Plan: Productos v3 — Fase 2, Tanda A (Merma / `yield_pct`)

## Summary
Agregar **merma (rendimiento) por ingrediente** al motor de food cost: `Ingredient.yield_pct` (bps, default 100%) y **costo efectivo = costo_crudo / yield_pct**. La clave de diseño: la merma se aplica al **construir el `cost_by_ingredient`** (costo efectivo por unidad usable), dejando `food_cost()` y `resolve_preparation_costs()` **intactos** → paridad garantizada para yield=100%, cero cambio en los números de Finanzas existentes. Migración 0022 (add column). Primera de 4 tandas de la Fase 2.

## User Story
Como **dueño (OWNER/MANAGER)**, quiero **cargar la merma de cada insumo** (200g de bife comprados no son 200g en el plato: hueso, grasa, cocción), para que **el food cost y el margen que veo sean reales y no estén subestimados 10–25%**.

## Problem → Solution
Hoy el costo asume rendimiento 100% (`costo_receta = qty × unit_cost`), subestimando proteínas/verduras → margen mentido para arriba. Con `yield_pct`: `costo_real = qty × (unit_cost / yield_pct)`. Se implementa como **costo efectivo por unidad usable** en la construcción del dict de costos.

## Metadata
- **Complexity**: Medium (~12 archivos; back + front)
- **Source PRD**: `.claude/PRPs/prds/productos-v3.prd.md` — Fase 2 (Ticket 1.2)
- **PRD Phase**: 2 (Tanda A de 4)
- **Estimated Files**: ~12
- **Migración**: **0022** (add column `ingredients.yield_pct`)

---

## Fase 2 — troceo en tandas (contexto)
| Tanda | Contenido | Estado |
|---|---|---|
| **2A — Merma (yield_pct)** | ESTE PLAN. Rendimiento por insumo → costo efectivo | pending |
| 2B — IVA neto | Guardar/consumir costo neto de IVA (reusar `split_vat`) | futuro |
| 2C — Conversión de unidades | Tabla de conversión por familia (kg↔g, L↔ml) | futuro |
| 2D — Versionado + costo de reposición | `recipe_version` + histórico de costo de insumo | futuro |

Se hace 2A primero porque es la de mayor impacto en la exactitud del margen y no depende de las otras.

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | `backend/app/domain/inventory/costing.py` | 13-43, 46-92 | `food_cost()` y `resolve_preparation_costs()`: **NO se tocan**. La merma entra por el dict de costos. Leer para confirmar la paridad. |
| P0 | `backend/app/domain/inventory/entities.py` | 42-83 | `Ingredient` (agregar `yield_pct` + property `effective_unit_cost`). `set_cost` last-cost. |
| P0 | `backend/app/domain/inventory/value_objects.py` | 5-20 | `QUANTITY_SCALE=1000`, `UnitOfMeasure`. Agregar `FULL_YIELD_BPS = 10000`. |
| P0 | `backend/app/domain/shared/money.py` | 13-49 | `Money` **frozen, no-negativo, sin sub/round**. El costeo hace `round()` sobre ints y construye `Money(total, cur)` directo. Copiar ese idioma. |
| P0 | `backend/app/infrastructure/persistence/food_cost_repo.py` | 64-75, 123-138 | Builder A de `cost_by_ingredient` (desde columnas ORM). Hay que traer `yield_pct` en el `select` y aplicar el costo efectivo. |
| P0 | `backend/app/application/analytics/projection.py` | 72-102 | Builder B de `cost_by_ingredient` (desde `ing.unit_cost` de dominio). Cambiar a `ing.effective_unit_cost`. **Ambos builders deben cambiar.** |
| P0 | `backend/app/infrastructure/persistence/models.py` | 423-440 | `IngredientORM` (agregar columna `yield_pct`). |
| P0 | `backend/app/infrastructure/persistence/mappers.py` | 590-615 | `ingredient_to_domain/orm` (mapear `yield_pct`). |
| P0 | `backend/app/application/inventory/use_cases.py` | 39-80, 129-168 | `CreateIngredient` / `UpdateIngredient` (aceptar `yield_pct`). |
| P0 | `backend/app/presentation/schemas/inventory.py` | `CreateIngredientRequest`, `UpdateIngredientRequest`, `IngredientResponse` | Agregar `yield_pct`. |
| P0 | `backend/app/presentation/api/v1/inventory.py` | create/update ingredient | Pasar `yield_pct`. |
| P0 | `backend/alembic/versions/0020_product_pricing.py` | 21-52 | Patrón `op.add_column(..., server_default=...)` + header de revisión. **Última migración = `0021_preparations`** → `down_revision="0021_preparations"`, id `0022_ingredient_yield`. |
| P1 | `frontend/src/api/types-inventory.ts` | 7-45 | `IngredientDTO`, `CreateIngredientBody`, `UpdateIngredientBody` (agregar `yield_pct`). |
| P1 | `frontend/src/api/inventory-api.ts` | create/update ingredient | Pasar `yield_pct`. |
| P1 | (localizar) el form de insumos | — | Buscar en `frontend/src/features/inventory` o `stock` el form de crear/editar ingrediente; agregar campo "Rendimiento (%)". |

## Patterns to Mirror

### DOMAIN — costo efectivo (property pura)
```python
# entities.py — agregar a Ingredient
from app.domain.inventory.value_objects import FULL_YIELD_BPS

@property
def effective_unit_cost(self) -> Money:
    """Costo por unidad USABLE: crudo / rendimiento (merma)."""
    if self.yield_pct >= FULL_YIELD_BPS:
        return self.unit_cost  # paridad exacta con 100%
    amount = round(self.unit_cost.amount * FULL_YIELD_BPS / self.yield_pct)
    return Money(amount, self.unit_cost.currency)
```
> Idioma idéntico al de `costing.py` / `taxation.py`: `round(x * 10000 / bps)`, construye `Money` directo.

### MIGRATION — add column (mirror 0020)
```python
# 0022_ingredient_yield.py
revision = "0022_ingredient_yield"
down_revision = "0021_preparations"

def upgrade() -> None:
    op.add_column(
        "ingredients",
        sa.Column("yield_pct", sa.Integer(), nullable=False, server_default="10000"),
    )

def downgrade() -> None:
    op.drop_column("ingredients", "yield_pct")
```

### READ MODEL — traer yield y aplicar costo efectivo (food_cost_repo.py)
```python
# reemplazar el select de cost_by_ingredient (líneas ~64-75)
rows = (await session.execute(
    select(
        IngredientORM.id,
        IngredientORM.unit_cost_amount,
        IngredientORM.unit_cost_currency,
        IngredientORM.yield_pct,
    ).where(IngredientORM.tenant_id == tenant_id)
)).all()
cost_by_ingredient = {
    iid: _effective(amount, cur, yld)  # helper local: round(amount*10000/yld)
    for iid, amount, cur, yld in rows
}
```

### TEST — paridad + merma
```python
# unit
def test_effective_cost_full_yield_is_identity(): ...   # yield 10000 → == unit_cost
def test_effective_cost_applies_merma():
    # unit_cost 1000, yield 8000 (80%) → 1250
    ing = _ingredient(unit_cost=1000, yield_pct=8000)
    assert ing.effective_unit_cost == Money(1250, "ARS")
def test_food_cost_unchanged_when_all_full_yield(): ...  # paridad con la suite actual
```

---

## Files to Change

| File | Action | Justificación |
|---|---|---|
| `backend/app/domain/inventory/value_objects.py` | UPDATE | `FULL_YIELD_BPS = 10000` |
| `backend/app/domain/inventory/entities.py` | UPDATE | `Ingredient.yield_pct` + `effective_unit_cost` |
| `backend/alembic/versions/0022_ingredient_yield.py` | CREATE | add column |
| `backend/app/infrastructure/persistence/models.py` | UPDATE | `IngredientORM.yield_pct` |
| `backend/app/infrastructure/persistence/mappers.py` | UPDATE | mapear `yield_pct` |
| `backend/app/infrastructure/persistence/food_cost_repo.py` | UPDATE | builder A → costo efectivo |
| `backend/app/application/analytics/projection.py` | UPDATE | builder B → `effective_unit_cost` |
| `backend/app/application/inventory/use_cases.py` | UPDATE | Create/Update aceptan `yield_pct` |
| `backend/app/presentation/schemas/inventory.py` | UPDATE | request/response con `yield_pct` |
| `backend/app/presentation/api/v1/inventory.py` | UPDATE | pasar `yield_pct` |
| `backend/tests/unit/test_*_costing*.py` + e2e inventory | UPDATE/CREATE | paridad + merma |
| `frontend/src/api/types-inventory.ts` + `inventory-api.ts` + form de insumo | UPDATE | campo "Rendimiento (%)" |

## NOT Building
- ❌ IVA neto (Tanda 2B), conversión de unidades (2C), versionado/costo de reposición (2D).
- ❌ Merma como evento monetizado (el `WASTE` sigue sin valuación; eso es otro tema).
- ❌ Defaults de merma por tipo de ingrediente (carne/verdura) — el spec los sugiere "editables"; en 2A el default es 100% y el dueño lo ajusta. Los presets van como mejora posterior.
- ❌ Recalcular food cost histórico de `sale_facts` ya persistido (el snapshot es al momento de venta; la merma aplica de acá en más). Un rebuild opcional se puede correr, no es parte de 2A.

---

## Step-by-Step Tasks

### Task 1 — Dominio: `yield_pct` + `effective_unit_cost`
- **ACTION**: `value_objects.py` agregar `FULL_YIELD_BPS = 10000`. `entities.py`: `Ingredient` agregar campo `yield_pct: int = FULL_YIELD_BPS` (después de `unit_cost`, antes de `active` para no romper posicional… **usar siempre kwargs**) + property `effective_unit_cost`.
- **IMPLEMENT**: ver patrón DOMAIN. Validar `yield_pct` en `1..10000` (agregar chequeo donde se cree/edite, o `__post_init__`; cuidado: `Ingredient` hoy no tiene `__post_init__` y agregarlo valida también al cargar de DB → si agrego `__post_init__`, las filas viejas ya tienen server_default 10000, OK). Preferir validar en el use case + schema para no arriesgar la carga.
- **MIRROR**: DOMAIN pattern.
- **GOTCHA**: `Money` es frozen y no acepta negativos; `effective_unit_cost` siempre ≥ `unit_cost` (yield ≤ 100%), nunca negativo. `Ingredient` es dataclass sin `__post_init__` — mantenerlo así; agregar `yield_pct` con default para no romper construcciones existentes.
- **VALIDATE**: unit tests de paridad + merma.

### Task 2 — Migración 0022
- **ACTION**: crear `0022_ingredient_yield.py`.
- **IMPLEMENT**: ver MIGRATION pattern. `down_revision="0021_preparations"`.
- **GOTCHA**: la columna es NOT NULL con `server_default="10000"` → filas existentes quedan en 100% (sin cambio de costo). Aplicar a dev: `poetry run alembic upgrade head`.
- **VALIDATE**: `alembic upgrade head` sin error; `\d ingredients` muestra `yield_pct`.

### Task 3 — ORM + mappers
- **ACTION**: `IngredientORM` add `yield_pct: Mapped[int] = mapped_column(Integer, server_default="10000")`; `ingredient_to_domain/orm` mapear.
- **MIRROR**: columnas existentes de `IngredientORM`; mappers `mappers.py:590-615`.
- **GOTCHA**: `ingredient_to_orm` no seteaba `created_at` (server_default) — mantener; agregar `yield_pct=ingredient.yield_pct`.
- **VALIDATE**: e2e crea insumo con yield y lo lee.

### Task 4 — Los DOS builders de costo
- **ACTION**: `food_cost_repo.py` (builder A) traer `yield_pct` en el select y construir costo efectivo; `projection.py` (builder B) cambiar `ing.unit_cost` → `ing.effective_unit_cost`.
- **MIRROR**: READ MODEL pattern.
- **GOTCHA**: **son dos lugares** (el reporte de food-cost y la proyección a `sale_facts`). Si sólo cambio uno, el drill-down y el snapshot divergen. `resolve_preparation_costs` recibe el `cost_by_ingredient` ya efectivo → la merma se propaga sola a las preparaciones anidadas. `food_cost()` **no se toca**.
- **VALIDATE**: e2e — subir merma de un insumo sube el food cost del plato y de la preparación que lo usa.

### Task 5 — Use cases + API
- **ACTION**: `CreateIngredient`/`UpdateIngredient` aceptan `yield_pct` (default 10000, validar 1..10000 → `InvalidQuantity` o nueva excepción `InvalidYield`); `schemas/inventory.py` request/response; `inventory.py` pasar el campo.
- **GOTCHA**: `UpdateIngredientRequest` hoy es name/min_qty/active → agregar `yield_pct: int | None`. Mantener retrocompat (omitido = sin cambio).
- **VALIDATE**: e2e PATCH yield.

### Task 6 — Frontend
- **ACTION**: `types-inventory.ts` (IngredientDTO + bodies con `yield_pct`), `inventory-api.ts` (pasar), y el **form de insumo** (localizar en `features/inventory`/`stock`): campo "Rendimiento (%)" (input, default 100), convertir % → bps (`Math.round(pct*100)`).
- **GOTCHA**: mostrar como % (100 = sin merma), guardar como bps. Aclarar en la UI: "cuánto del insumo llega al plato (100% = sin desperdicio)".
- **VALIDATE**: `npm run build` + set merma desde la UI mueve el food cost.

### Task 7 — Tests
- **ACTION**: unit (`effective_unit_cost` paridad + merma; food_cost con todos-100% == suite actual) + e2e inventory (crear con yield, PATCH yield, propagación a food-cost y a preparación).
- **MIRROR**: `tests/unit/test_preparations_costing.py` (paridad), `tests/integration/test_e2e_preparations_api.py` (propagación 150→300).
- **GOTCHA**: `asyncio_mode=auto`. Verificar que la **suite completa** sigue verde (paridad: nada cambia con yield=100%).
- **VALIDATE**: `poetry run pytest` completo + `ruff`.

---

## Testing Strategy
| Test | Input | Expected |
|---|---|---|
| `effective_unit_cost` identidad | unit_cost 1000, yield 10000 | Money(1000) |
| `effective_unit_cost` merma | unit_cost 1000, yield 8000 | Money(1250) |
| food_cost paridad | receta con insumos yield 100% | igual que suite actual |
| e2e propagación merma | subir merma insumo base | food cost plato y preparación suben |
| PATCH yield | update yield_pct | persiste y recalcula |

### Edge Cases
- [x] yield 10000 (100%) → costo idéntico (paridad, no rompe Finanzas).
- [x] yield inválido (0, >10000, negativo) → 422.
- [x] Merma en insumo dentro de una preparación anidada → propaga.
- [x] Insumo sin receta → sin efecto.

## Validation Commands
```bash
cd backend && poetry run alembic upgrade head          # aplica 0022 a dev
cd backend && poetry run ruff check --fix && poetry run pytest   # suite completa (paridad)
cd frontend && npm run build && npm run test && npm run lint
```

## Acceptance Criteria
- [ ] `Ingredient.yield_pct` (default 100%) + `effective_unit_cost`.
- [ ] Los DOS builders aplican costo efectivo; `food_cost()` intacto.
- [ ] Migración 0022 aplicada; paridad total con yield=100% (suite verde sin cambios).
- [ ] API + form permiten setear la merma; sube el food cost del plato y de las preparaciones.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Cambiar el costeo altera números de Finanzas en prod | Baja | Alto | Merma vía costo efectivo + default 100% → **paridad exacta**; test de paridad + suite completa |
| Cambiar sólo un builder → drill-down ≠ snapshot | Media | Medio | Task 4 cambia **ambos** explícitamente; e2e cubre los dos caminos |
| `__post_init__` nuevo en Ingredient rompe carga de filas viejas | Baja | Medio | No agregar `__post_init__`; validar en use case/schema |

## Notes
- **Por qué costo efectivo y no tocar `food_cost()`**: mantener el motor puro sin cambios preserva la paridad (Finanzas ya en prod) y hace que la merma se propague sola a preparaciones anidadas vía `resolve_preparation_costs`. Es el mismo criterio que la Tanda C de Productos v2 (extender por los bordes, no romper el núcleo).
- **Histórico de costo de insumo**: hoy sólo existe en `stock_movements.unit_cost_amount` (filas PURCHASE). El costo de reposición + histórico formal es **Tanda 2D**, no acá.
- **Sin `Decimal`/float** en ningún lado: enteros + `round(x*10000/bps)`.
