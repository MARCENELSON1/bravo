from __future__ import annotations

from app.domain.errors import DomainError


class IngredientNotFound(DomainError):
    code = "ingredient_not_found"
    message = "No encontramos el insumo indicado."


class SupplierNotFound(DomainError):
    code = "supplier_not_found"
    message = "No encontramos el proveedor indicado."


class RecipeNotFound(DomainError):
    code = "recipe_not_found"
    message = "Este producto no tiene receta cargada."


class InvalidQuantity(DomainError):
    code = "invalid_quantity"
    message = "La cantidad debe ser mayor que cero."


class InvalidUnitCost(DomainError):
    code = "invalid_unit_cost"
    message = "El costo del insumo debe ser mayor que cero."


class InvalidRecipeComponent(DomainError):
    """Un ítem de receta apunta a un insumo O a una preparación, exactamente uno."""

    code = "invalid_recipe_component"
    message = "Cada ítem debe ser un insumo o una preparación, no ambos."


class RecipeCycle(DomainError):
    """Una preparación no puede depender de sí misma (directa o indirectamente)."""

    code = "recipe_cycle"
    message = "Las preparaciones no pueden formar un ciclo."


class PreparationNotFound(DomainError):
    code = "preparation_not_found"
    message = "No encontramos la preparación indicada."


class IncompatibleUnits(DomainError):
    """La unidad de receta debe ser la del insumo o su sub-unidad fina (KG→G, L→ML)."""

    code = "incompatible_units"
    message = "La unidad de receta debe ser la del insumo o su sub-unidad (kg→g, l→ml)."
