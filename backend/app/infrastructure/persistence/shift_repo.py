from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.domain.timeclock.entities import Shift
from app.domain.timeclock.repository import ShiftRepository
from app.domain.timeclock.value_objects import ShiftStatus
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import shift_to_domain, shift_to_orm
from app.infrastructure.persistence.models import ShiftORM


class SqlAlchemyShiftRepository(ShiftRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_open_for_user(self, tenant_id: str, user_id: str) -> Shift | None:
        async with self._session_factory() as session:
            stmt = (
                select(ShiftORM)
                .where(
                    ShiftORM.tenant_id == tenant_id,
                    ShiftORM.user_id == user_id,
                    ShiftORM.status == ShiftStatus.OPEN.value,
                )
                .order_by(ShiftORM.clock_in_at.desc())
            )
            row = (await session.execute(stmt)).scalars().first()
            return shift_to_domain(row) if row is not None else None

    async def get_by_id(self, tenant_id: str, shift_id: str) -> Shift | None:
        async with self._session_factory() as session:
            stmt = select(ShiftORM).where(
                ShiftORM.id == shift_id, ShiftORM.tenant_id == tenant_id
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return shift_to_domain(row) if row is not None else None

    async def list(
        self,
        tenant_id: str,
        *,
        user_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[Shift]:
        async with self._session_factory() as session:
            stmt = select(ShiftORM).where(ShiftORM.tenant_id == tenant_id)
            if user_id is not None:
                stmt = stmt.where(ShiftORM.user_id == user_id)
            if since is not None:
                stmt = stmt.where(ShiftORM.clock_in_at >= since)
            if until is not None:
                stmt = stmt.where(ShiftORM.clock_in_at <= until)
            stmt = stmt.order_by(ShiftORM.clock_in_at.desc())
            rows = (await session.execute(stmt)).scalars().all()
            return [shift_to_domain(row) for row in rows]

    async def add(self, shift: Shift) -> None:
        async with self._session_factory() as session:
            session.add(shift_to_orm(shift))

    async def save(self, shift: Shift) -> None:
        async with self._session_factory() as session:
            await session.merge(shift_to_orm(shift))
