from __future__ import annotations

from app.domain.errors import DomainError


class SessionNotFound(DomainError):
    code = "session_not_found"
    message = "No encontramos la sesión de mesa indicada."


class SectorNotFound(DomainError):
    code = "sector_not_found"
    message = "No encontramos el sector indicado."


class TableAlreadyAssigned(DomainError):
    code = "table_already_assigned"
    message = "La mesa ya tiene un mozo a cargo."


class SessionHasActiveOrders(DomainError):
    """Can't close a table with a live order: pay or cancel it first."""

    code = "session_has_active_orders"
    message = "La mesa tiene una comanda activa: cobrala o anulala antes de cerrarla."


class NothingToCharge(DomainError):
    """Asking for the bill of a table with nothing ordered."""

    code = "nothing_to_charge"
    message = "La mesa no tiene nada para cobrar."
