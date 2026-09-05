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


class ItemNotPending(DomainError):
    code = "item_not_pending"
    message = "Solo se puede modificar un ítem que todavía no fue marchado."


class InvalidItemTransition(DomainError):
    code = "invalid_item_transition"
    message = "El ítem no puede cambiar a ese estado."


class OrderHasAuthorizedInvoice(DomainError):
    code = "order_has_authorized_invoice"
    message = (
        "No se puede reabrir: la comanda ya tiene un comprobante fiscal autorizado. "
        "Emití una nota de crédito."
    )


class OrderNotFullyPaid(DomainError):
    code = "order_not_fully_paid"
    message = "No se puede liberar la mesa: la comanda todavía tiene saldo a cobrar."


class SelfOrderDisabled(DomainError):
    code = "self_order_disabled"
    message = "El autopedido no está habilitado en este local."


class NoCourseToFire(DomainError):
    """"Marchar siguiente" with nothing held: every course is already fired."""

    code = "no_course_to_fire"
    message = "No hay un tiempo en espera para marchar."
