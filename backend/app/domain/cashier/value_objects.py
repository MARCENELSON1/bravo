from __future__ import annotations

from enum import StrEnum


class CashSessionStatus(StrEnum):
    """Lifecycle of a register session (turno de caja)."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
