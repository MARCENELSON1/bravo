"""Base domain error.

Every domain exception carries a stable English ``code`` (for clients/logs) and
a user-facing Spanish ``message``. The presentation layer maps each error type
to an HTTP status and returns ``{code, message}``.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain errors."""

    code: str = "domain_error"
    message: str = "Ocurrió un error inesperado."

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)
