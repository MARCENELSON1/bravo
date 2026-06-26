from __future__ import annotations

from app.domain.errors import DomainError


class OrderNotFound(DomainError):
    code = "order_not_found"
    message = "No encontramos la comanda indicada."


class InvalidOrderTransition(DomainError):
    code = "invalid_order_transition"
    message = "La comanda no puede cambiar a ese estado."


class EmptyOrder(DomainError):
    code = "empty_order"
    message = "No se puede enviar una comanda sin ítems."


class ItemNotFound(DomainError):
    code = "item_not_found"
    message = "No encontramos el ítem en la comanda."


class InvalidItemQuantity(DomainError):
    code = "invalid_item_quantity"
    message = "La cantidad del ítem no es válida."
