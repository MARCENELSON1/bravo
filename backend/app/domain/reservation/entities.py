from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.reservation.exceptions import (
    InvalidPartySize,
    InvalidReservationTransition,
)
from app.domain.reservation.value_objects import ReservationStatus, ServiceTurn

# States from which no transition is allowed.
_TERMINAL = frozenset(
    {ReservationStatus.COMPLETED, ReservationStatus.CANCELLED, ReservationStatus.NO_SHOW}
)


@dataclass
class Reservation:
    """A table reservation (reserva) for a service turn, scoped to a tenant.

    ``table_id`` is optional (a reservation can be unassigned until seated). The
    lifecycle is enforced here; ``reserved_at`` is the desired date/time provided
    by the client, ``created_at`` is set by the server.
    """

    id: str
    tenant_id: str
    customer_name: str
    party_size: int
    reserved_at: datetime
    turn: ServiceTurn
    customer_phone: str | None = None
    table_id: str | None = None
    status: ReservationStatus = ReservationStatus.PENDING
    note: str | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.party_size <= 0:
            raise InvalidPartySize()

    def _require(self, *allowed: ReservationStatus) -> None:
        if self.status not in allowed:
            raise InvalidReservationTransition()

    def confirm(self) -> None:
        self._require(ReservationStatus.PENDING)
        self.status = ReservationStatus.CONFIRMED

    def seat(self) -> None:
        self._require(ReservationStatus.PENDING, ReservationStatus.CONFIRMED)
        self.status = ReservationStatus.SEATED

    def complete(self) -> None:
        self._require(ReservationStatus.SEATED)
        self.status = ReservationStatus.COMPLETED

    def cancel(self) -> None:
        self._require(ReservationStatus.PENDING, ReservationStatus.CONFIRMED)
        self.status = ReservationStatus.CANCELLED

    def mark_no_show(self) -> None:
        self._require(ReservationStatus.PENDING, ReservationStatus.CONFIRMED)
        self.status = ReservationStatus.NO_SHOW

    def reschedule(
        self,
        *,
        reserved_at: datetime,
        turn: ServiceTurn,
        party_size: int,
        table_id: str | None,
    ) -> None:
        """Edit the reservation's data while it is not in a terminal state."""
        if self.status in _TERMINAL:
            raise InvalidReservationTransition()
        if party_size <= 0:
            raise InvalidPartySize()
        self.reserved_at = reserved_at
        self.turn = turn
        self.party_size = party_size
        self.table_id = table_id
