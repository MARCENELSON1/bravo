from __future__ import annotations

from app.domain.errors import DomainError


class ProductNotFound(DomainError):
    code = "product_not_found"
    message = "No encontramos el producto."


class InactiveProduct(DomainError):
    code = "inactive_product"
    message = "El producto no está disponible."
