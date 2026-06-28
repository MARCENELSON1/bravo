from __future__ import annotations

from app.domain.errors import DomainError


class CashSessionNotFound(DomainError):
    code = "cash_session_not_found"
    message = "No encontramos la caja indicada."


class CashSessionAlreadyOpen(DomainError):
    code = "cash_session_already_open"
    message = "Ya hay una caja abierta. Cerrala antes de abrir otra."


class CashSessionAlreadyClosed(DomainError):
    code = "cash_session_already_closed"
    message = "La caja ya está cerrada."
