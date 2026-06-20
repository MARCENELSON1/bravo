from __future__ import annotations

from enum import StrEnum


class OrderStatus(StrEnum):
    """Lifecycle of an order (comanda)."""

    OPEN = "OPEN"
    SENT = "SENT"
    PREPARING = "PREPARING"
    READY = "READY"
    SERVED = "SERVED"
    CANCELLED = "CANCELLED"
