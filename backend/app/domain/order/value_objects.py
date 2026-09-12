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
    # Marched but held for a later course: the kitchen SEES it (mise en place)
    # but does not cook it until the waiter fires that course.
    HELD = "HELD"
    SENT = "SENT"
    PREPARING = "PREPARING"
    READY = "READY"
    SERVED = "SERVED"
    CANCELLED = "CANCELLED"


class Course(StrEnum):
    """Service course a plate belongs to — a property of the PRODUCT (set once
    in the catalog), copied onto the line so the waiter can override a plate
    ("la provoleta como principal"). The kitchen cooks one course at a time:
    starters first, mains when the waiter fires them, then desserts. IMMEDIATE
    = no coursing at all (bar, anything that goes out right away)."""

    IMMEDIATE = "IMMEDIATE"
    STARTER = "STARTER"
    MAIN = "MAIN"
    DESSERT = "DESSERT"

    @property
    def sequence(self) -> int:
        return _COURSE_SEQUENCE[self]

    @property
    def coursed(self) -> bool:
        """Takes part in the starter → main → dessert sequence."""
        return self is not Course.IMMEDIATE


_COURSE_SEQUENCE: dict[Course, int] = {
    Course.IMMEDIATE: 0,
    Course.STARTER: 1,
    Course.MAIN: 2,
    Course.DESSERT: 3,
}


class CourseState(StrEnum):
    """Derived state of one course inside an order (never stored)."""

    PENDING = "PENDING"  # loaded, not marched
    HELD = "HELD"  # marched, waiting for the waiter to fire it
    IN_KITCHEN = "IN_KITCHEN"  # fired: being cooked
    READY = "READY"  # every fired plate is ready → serve the course
    SERVED = "SERVED"


class Station(StrEnum):
    """Where an item is prepared. Routes items to the right KDS board."""

    KITCHEN = "KITCHEN"
    BAR = "BAR"


class OrderSource(StrEnum):
    """Who originated the order. Defaults to WAITER (parity); CUSTOMER_QR marks an
    order the diner placed from the QR menu (Carta QR F2) — for metrics + the gate.
    CUSTOMER_QR_PREPAID (Fase 3, Self-service) is a QR order held off the kitchen
    until it's paid: it stays out of the "QR por confirmar" tray and the payment
    webhook marches + auto-assigns it."""

    WAITER = "WAITER"
    CUSTOMER_QR = "CUSTOMER_QR"
    CUSTOMER_QR_PREPAID = "CUSTOMER_QR_PREPAID"


# Sentinel del mozo cuando una orden nace sin dueño humano (autopedido QR que abre
# la mesa): UUID nil en la columna (sin FK). El significado lo porta `source`; una
# sesión con este waiter cuenta como "huérfana" y se reasigna al confirmar.
CUSTOMER_WAITER_ID = "00000000-0000-0000-0000-000000000000"
