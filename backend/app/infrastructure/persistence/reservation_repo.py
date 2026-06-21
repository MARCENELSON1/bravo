from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.domain.reservation.entities import Reservation
from app.domain.reservation.repository import ReservationRepository
from app.domain.reservation.value_objects import ReservationStatus, ServiceTurn
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    reservation_to_domain,
    reservation_to_orm,
)
from app.infrastructure.persistence.models import ReservationORM


class SqlAlchemyReservationRepository(ReservationRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, tenant_id: str, reservation_id: str) -> Reservation | None:
        async with self._session_factory() as session:
            stmt = select(ReservationORM).where(
                ReservationORM.id == reservation_id,
                ReservationORM.tenant_id == tenant_id,
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return reservation_to_domain(row) if row is not None else None

    async def list(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        turn: ServiceTurn | None = None,
        status: ReservationStatus | None = None,
        table_id: str | None = None,
    ) -> list[Reservation]:
        async with self._session_factory() as session:
            stmt = select(ReservationORM).where(ReservationORM.tenant_id == tenant_id)
            if since is not None:
                stmt = stmt.where(ReservationORM.reserved_at >= since)
            if until is not None:
                stmt = stmt.where(ReservationORM.reserved_at <= until)
            if turn is not None:
                stmt = stmt.where(ReservationORM.turn == turn.value)
            if status is not None:
                stmt = stmt.where(ReservationORM.status == status.value)
            if table_id is not None:
                stmt = stmt.where(ReservationORM.table_id == table_id)
            stmt = stmt.order_by(ReservationORM.reserved_at)
            rows = (await session.execute(stmt)).scalars().all()
            return [reservation_to_domain(row) for row in rows]

    async def add(self, reservation: Reservation) -> None:
        async with self._session_factory() as session:
            session.add(reservation_to_orm(reservation))

    async def save(self, reservation: Reservation) -> None:
        async with self._session_factory() as session:
            await session.merge(reservation_to_orm(reservation))
