from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.inventory.value_objects import UnitOfMeasure

# Quantities are integers in milésimas of the base unit (e.g. 1500 = 1.5 kg).
# Costs are Money minor units per one base unit (e.g. centavos per kg).


class CreateIngredientRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    unit: UnitOfMeasure
    min_qty: int = Field(default=0, ge=0)
    unit_cost_amount: int = Field(gt=0)
    stock_qty: int = Field(default=0, ge=0)


class UpdateIngredientRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    min_qty: int | None = Field(default=None, ge=0)
    active: bool | None = None


class IngredientResponse(BaseModel):
    id: str
    name: str
    unit: str
    stock_qty: int
    min_qty: int
    unit_cost_amount: int
    currency: str
    active: bool
    is_below_min: bool


class CreateIngredientResponse(BaseModel):
    ingredient_id: str


class PurchaseRequest(BaseModel):
    qty: int = Field(gt=0)
    unit_cost_amount: int = Field(gt=0)


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
    ingredient_id: str
    qty: int = Field(gt=0)


class SetRecipeRequest(BaseModel):
    items: list[RecipeItemSchema]


class RecipeResponse(BaseModel):
    product_id: str
    has_recipe: bool
    items: list[RecipeItemSchema]
