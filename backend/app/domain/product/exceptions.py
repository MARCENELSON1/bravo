from __future__ import annotations

from app.domain.errors import DomainError


class ProductNotFound(DomainError):
    code = "product_not_found"
    message = "No encontramos el producto."


class InactiveProduct(DomainError):
    code = "inactive_product"
    message = "El producto no está disponible."


class ProductUnavailable(DomainError):
    code = "product_unavailable"
    message = "Ese plato hoy no está disponible."


class InvalidModifierGroup(DomainError):
    code = "invalid_modifier_group"
    message = "El grupo de opciones no es válido."


class InvalidModifierSelection(DomainError):
    code = "invalid_modifier_selection"
    message = "Revisá las opciones elegidas del plato."
