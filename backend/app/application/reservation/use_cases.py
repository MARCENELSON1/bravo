"""Reservation CRUD + lifecycle transitions + agenda listing.

Use cases depend on domain ports only and set the tenant context first so
Postgres RLS applies. Transitions load the aggregate, mutate it (which enforces
the lifecycle) and persist.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.domain.identity.ports import TenantContext
from app.domain.reservation.entities import Reservation
from app.domain.reservation.exceptions import ReservationNotFound
from app.domain.reservation.repository import ReservationRepository
from app.domain.reservation.value_objects import ReservationStatus, ServiceTurn
from app.domain.table.exceptions import TableNotFound
from app.domain.table.repository import TableRepository


class CreateReservation:
    """Create a reservation for a service turn. If a table is given, it must
    exist for the tenant; party-size validation lives in the entity."""

    def __init__(
        self,
        reservations: ReservationRepository,
        tables: TableRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._reservations = reservations
        self._tables = tables
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        customer_name: str,
        party_size: int,
        reserved_at: datetime,
        turn: ServiceTurn,
        customer_phone: str | None = None,
        table_id: str | None = None,
        note: str | None = None,
    ) -> Reservation:
        self._tenant_context.set(tenant_id)
        if table_id is not None and await self._tables.get_by_id(tenant_id, table_id) is None:
            raise TableNotFound()
        reservation = Reservation(
            id=str(uuid4()),
            tenant_id=tenant_id,
            customer_name=customer_name,
            party_size=party_size,
            reserved_at=reserved_at,
            turn=turn,
            customer_phone=customer_phone,
            table_id=table_id,
            note=note,
        )
        await self._reservations.add(reservation)
        return reservation


class ListReservations:
    """Agenda: reservations filtered by day/turn/status/table, ordered by time."""

    def __init__(
        self, reservations: ReservationRepository, tenant_context: TenantContext
    ) -> None:
        self._reservations = reservations
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
        turn: ServiceTurn | None = None,
        status: ReservationStatus | None = None,
        table_id: str | None = None,
    ) -> list[Reservation]:
        self._tenant_context.set(tenant_id)
        return await self._reservations.list(
            tenant_id,
            since=since,
            until=until,
            turn=turn,
            status=status,
            table_id=table_id,
        )


class GetReservation:
    def __init__(
        self, reservations: ReservationRepository, tenant_context: TenantContext
    ) -> None:
        self._reservations = reservations
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, reservation_id: str) -> Reservation:
        self._tenant_context.set(tenant_id)
        reservation = await self._reservations.get_by_id(tenant_id, reservation_id)
        if reservation is None:
            raise ReservationNotFound()
        return reservation


class _ReservationTransition:
    """Base for the lifecycle transitions: load → mutate → save."""

    def __init__(
        self, reservations: ReservationRepository, tenant_context: TenantContext
    ) -> None:
        self._reservations = reservations
        self._tenant_context = tenant_context

    async def _apply(self, tenant_id: str, reservation_id: str, action: str) -> Reservation:
        self._tenant_context.set(tenant_id)
        reservation = await self._reservations.get_by_id(tenant_id, reservation_id)
        if reservation is None:
            raise ReservationNotFound()
        getattr(reservation, action)()  # raises InvalidReservationTransition if illegal
        await self._reservations.save(reservation)
        return reservation


class ConfirmReservation(_ReservationTransition):
    async def execute(self, *, tenant_id: str, reservation_id: str) -> Reservation:
        return await self._apply(tenant_id, reservation_id, "confirm")


class SeatReservation(_ReservationTransition):
    async def execute(self, *, tenant_id: str, reservation_id: str) -> Reservation:
        return await self._apply(tenant_id, reservation_id, "seat")


class CompleteReservation(_ReservationTransition):
    async def execute(self, *, tenant_id: str, reservation_id: str) -> Reservation:
        return await self._apply(tenant_id, reservation_id, "complete")


class CancelReservation(_ReservationTransition):
    async def execute(self, *, tenant_id: str, reservation_id: str) -> Reservation:
        return await self._apply(tenant_id, reservation_id, "cancel")


class MarkNoShow(_ReservationTransition):
    async def execute(self, *, tenant_id: str, reservation_id: str) -> Reservation:
        return await self._apply(tenant_id, reservation_id, "mark_no_show")


class UpdateReservation:
    """Reschedule / reassign a reservation (rejected once it is terminal)."""

    def __init__(
        self,
        reservations: ReservationRepository,
        tables: TableRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._reservations = reservations
        self._tables = tables
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        reservation_id: str,
        reserved_at: datetime,
        turn: ServiceTurn,
        party_size: int,
        table_id: str | None,
    ) -> Reservation:
        self._tenant_context.set(tenant_id)
        reservation = await self._reservations.get_by_id(tenant_id, reservation_id)
        if reservation is None:
            raise ReservationNotFound()
        if table_id is not None and await self._tables.get_by_id(tenant_id, table_id) is None:
            raise TableNotFound()
        reservation.reschedule(
            reserved_at=reserved_at, turn=turn, party_size=party_size, table_id=table_id
        )
        await self._reservations.save(reservation)
        return reservation
