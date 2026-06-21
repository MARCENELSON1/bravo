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
