from __future__ import annotations

from app.domain.errors import DomainError


class SessionNotFound(DomainError):
    code = "session_not_found"
    message = "No encontramos la sesión de mesa indicada."
