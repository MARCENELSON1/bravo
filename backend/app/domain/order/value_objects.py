from __future__ import annotations

from enum import StrEnum


class OrderStatus(StrEnum):
    """Lifecycle of an order (comanda).

    This is now *derived* from the per-item lifecycle (see ``ItemStatus``): the
    order rolls up to the least-advanced stage of its non-cancelled items. PAID
    and CANCELLED stay explicit order-level terminal states (never derived).
    """

    OPEN = "OPEN"
    SENT = "SENT"
    PREPARING = "PREPARING"
    READY = "READY"
    SERVED = "SERVED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class ItemStatus(StrEnum):
    """Per-item kitchen lifecycle. Lets a single order carry multiple rounds and
    bump items one by one (the backbone of station routing + multi-round)."""

    PENDING = "PENDING"  # loaded on the comanda, not yet sent ("marchado")
    SENT = "SENT"
    PREPARING = "PREPARING"
    READY = "READY"
    SERVED = "SERVED"
    CANCELLED = "CANCELLED"


class Station(StrEnum):
    """Where an item is prepared. Routes items to the right KDS board."""

    KITCHEN = "KITCHEN"
    BAR = "BAR"
