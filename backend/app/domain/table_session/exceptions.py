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
