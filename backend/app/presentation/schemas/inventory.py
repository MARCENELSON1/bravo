from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.domain.inventory.value_objects import UnitOfMeasure

# Quantities are integers in milésimas of the base unit (e.g. 1500 = 1.5 kg).
# Costs are Money minor units per one base unit (e.g. centavos per kg).


class CreateIngredientRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    unit: UnitOfMeasure
    min_qty: int = Field(default=0, ge=0)
    unit_cost_amount: int = Field(gt=0)
    stock_qty: int = Field(default=0, ge=0)
    # Yield/merma in basis points (10000 = 100% = no loss).
    yield_pct: int = Field(default=10000, ge=1, le=10000)
    # Does the loaded cost include VAT? (responsable inscripto). False = monotributo.
    price_includes_tax: bool = True
    # Recipe unit (Fase 2C): finer same-family sub-unit for recipes (KG→G, L→ML).
    # None = base unit. Validated server-side; set only at creation.
    recipe_unit: UnitOfMeasure | None = None


class UpdateIngredientRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    min_qty: int | None = Field(default=None, ge=0)
    active: bool | None = None
    yield_pct: int | None = Field(default=None, ge=1, le=10000)
    cost_includes_tax: bool | None = None  # editar la clasificación de IVA


class IngredientResponse(BaseModel):
    id: str
    name: str
    unit: str
    stock_qty: int
    min_qty: int
    unit_cost_amount: int
    currency: str
    yield_pct: int
    cost_includes_tax: bool
    recipe_unit: str | None
    active: bool
    is_below_min: bool


class IngredientCostPointResponse(BaseModel):
    """Fase 2D: un punto del histórico de costo de un insumo (una compra)."""

    occurred_at: str
    unit_cost_amount: int
    currency: str


class CreateIngredientResponse(BaseModel):
    ingredient_id: str


class PurchaseRequest(BaseModel):
    qty: int = Field(gt=0)
    unit_cost_amount: int = Field(gt=0)
    # None = no toca la clasificación de IVA del insumo (un restock no la pisa).
    price_includes_tax: bool | None = None


class WasteRequest(BaseModel):
    qty: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=255)


class CreateSupplierRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    contact: str | None = Field(default=None, max_length=255)


class SupplierResponse(BaseModel):
    id: str
    name: str
    contact: str | None
    active: bool


class CreateSupplierResponse(BaseModel):
    supplier_id: str


class RecipeItemSchema(BaseModel):
    """Un ítem de receta/preparación: un insumo O una preparación, no ambos."""

    ingredient_id: str | None = None
    preparation_id: str | None = None
    qty: int = Field(gt=0)

    @model_validator(mode="after")
    def _exactly_one_component(self) -> RecipeItemSchema:
        if (self.ingredient_id is None) == (self.preparation_id is None):
            raise ValueError("indicá un insumo o una preparación, no ambos")
        return self


class SetRecipeRequest(BaseModel):
    items: list[RecipeItemSchema]


class RecipeResponse(BaseModel):
    product_id: str
    has_recipe: bool
    items: list[RecipeItemSchema]
    version: int = 1  # Fase 2D: versión de la receta (incrementa en cada guardado)


# --- Preparaciones (recetas madre) ------------------------------------------


class SavePreparationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    yield_qty: int = Field(gt=0)  # rendimiento en milésimas de la unidad de la prep
    items: list[RecipeItemSchema]


class PreparationResponse(BaseModel):
    id: str
    name: str
    yield_qty: int
    used_in_products: int = 0  # en cuántos platos se usa
    items: list[RecipeItemSchema]


class CreatePreparationResponse(BaseModel):
    preparation_id: str


class FoodCostRowResponse(BaseModel):
    product_id: str
    product_name: str
    price_amount: int
    food_cost_amount: int
    margin_amount: int  # may be negative (sold below cost)
    food_cost_ratio_bps: int
    currency: str
    cost_confirmed: bool  # Fase 3: todo el food cost respaldado por compras
    coverage_bps: int  # Fase 3: cobertura de costo confirmado (bps)


class FoodCostResponse(BaseModel):
    currency: str
    rows: list[FoodCostRowResponse]
    coverage_bps: int = 10000  # Fase 3: cobertura del tenant (platos confirmados)
    confirmed_count: int = 0
    total_count: int = 0
    coverage_ok: bool = True  # Fase 6: ¿la cobertura llega al umbral del hero?
