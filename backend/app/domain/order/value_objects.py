from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class SelectedOption:
    """A modifier option chosen for an order line, snapshotted at order time (ej.
    "+Panceta", price_delta 1200). Display-only: the ``price_delta`` is already
    folded into the item's ``unit_price``, so the money math never re-reads it —
    this list just lets the kitchen ticket show the plate's personalisation."""

    option_id: str
    name: str
    price_delta: int


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


class OrderSource(StrEnum):
    """Who originated the order. Defaults to WAITER (parity); CUSTOMER_QR marks an
    order the diner placed from the QR menu (Carta QR F2) — for metrics + the gate."""

    WAITER = "WAITER"
    CUSTOMER_QR = "CUSTOMER_QR"
