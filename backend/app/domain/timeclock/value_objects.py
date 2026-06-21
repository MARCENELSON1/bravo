from __future__ import annotations

from enum import StrEnum


class ShiftStatus(StrEnum):
    """Lifecycle of a shift (turno): open until the worker clocks out."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"


class ShiftSource(StrEnum):
    """How the punch was registered (for audit)."""

    SELF = "SELF"  # toggle from the worker's own session
    PRESENCE = "PRESENCE"  # validated rotating QR / typeable code
    MANAGER = "MANAGER"  # manual correction by OWNER/MANAGER
