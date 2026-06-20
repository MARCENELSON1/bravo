from __future__ import annotations

from app.domain.errors import DomainError


class TableNotFound(DomainError):
    code = "table_not_found"
    message = "No encontramos la mesa indicada."
