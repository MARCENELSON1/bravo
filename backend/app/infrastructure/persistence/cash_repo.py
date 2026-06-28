from __future__ import annotations

from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.cashier.entities import CashSession
from app.domain.cashier.repository import CashSessionRepository
from app.domain.cashier.value_objects import CashSessionStatus
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    cash_count_to_orm,
    cash_session_to_domain,
    cash_session_to_orm,
)
from app.infrastructure.persistence.models import CashCountORM, CashSessionORM


class SqlAlchemyCashSessionRepository(CashSessionRepository):
    """Aggregate repo (session + counts). Every query is scoped by ``tenant_id``."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def _load(self, db: AsyncSession, row: CashSessionORM) -> CashSession:
        counts = (
            await db.execute(
                select(CashCountORM).where(
                    CashCountORM.cash_session_id == row.id,
                    CashCountORM.tenant_id == row.tenant_id,
                )
            )
        ).scalars().all()
        return cash_session_to_domain(row, list(counts))

    async def get_by_id(self, tenant_id: str, session_id: str) -> CashSession | None:
        async with self._session_factory() as db:
            row = (
                await db.execute(
                    select(CashSessionORM).where(
                        CashSessionORM.id == session_id,
                        CashSessionORM.tenant_id == tenant_id,
                    )
                )
            ).scalar_one_or_none()
            return await self._load(db, row) if row is not None else None

    async def get_open(self, tenant_id: str) -> CashSession | None:
        async with self._session_factory() as db:
            row = (
                await db.execute(
                    select(CashSessionORM).where(
                        CashSessionORM.tenant_id == tenant_id,
                        CashSessionORM.status == CashSessionStatus.OPEN.value,
                    )
                )
            ).scalar_one_or_none()
            return await self._load(db, row) if row is not None else None

    async def add(self, session: CashSession) -> None:
        async with self._session_factory() as db:
            db.add(cash_session_to_orm(session))

    async def save(self, session: CashSession) -> None:
        async with self._session_factory() as db:
            await db.merge(cash_session_to_orm(session))
            await db.execute(
                delete(CashCountORM).where(
                    CashCountORM.cash_session_id == session.id,
                    CashCountORM.tenant_id == session.tenant_id,
                )
            )
            for count in session.counts:
                db.add(cash_count_to_orm(count, session, str(uuid4())))
