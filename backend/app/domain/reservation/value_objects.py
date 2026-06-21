from __future__ import annotations

from enum import StrEnum


class ReservationStatus(StrEnum):
    """Lifecycle of a reservation (reserva).

    PENDING → CONFIRMED → SEATED → COMPLETED is the happy path; CANCELLED and
    NO_SHOW are terminal off-ramps. The party can be SEATED straight from
    PENDING (a walk-in confirmed on arrival).
    """

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SEATED = "SEATED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class ServiceTurn(StrEnum):
    """Dining service slot (turno). UX: 'Almuerzo' / 'Cena'."""

    LUNCH = "LUNCH"
    DINNER = "DINNER"
