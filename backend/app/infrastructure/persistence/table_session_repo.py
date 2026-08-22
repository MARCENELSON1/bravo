from __future__ import annotations

from sqlalchemy import select

from app.domain.table_session.entities import TableSession
from app.domain.table_session.repository import TableSessionRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    table_session_to_domain,
    table_session_to_orm,
)
from app.infrastructure.persistence.models import TableSessionORM


class SqlAlchemyTableSessionRepository(TableSessionRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS).
    "Open" = not closed and not merged away."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, tenant_id: str, session_id: str) -> TableSession | None:
        async with self._session_factory() as session:
            stmt = select(TableSessionORM).where(
                TableSessionORM.id == session_id,
                TableSessionORM.tenant_id == tenant_id,
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return table_session_to_domain(row) if row is not None else None

    async def get_open_by_table(
        self, tenant_id: str, table_id: str
    ) -> TableSession | None:
        async with self._session_factory() as session:
            stmt = (
                select(TableSessionORM)
                .where(
                    TableSessionORM.tenant_id == tenant_id,
                    TableSessionORM.table_id == table_id,
                    TableSessionORM.closed_at.is_(None),
                    TableSessionORM.merged_into_id.is_(None),
                )
                .order_by(TableSessionORM.opened_at.asc())
            )
            row = (await session.execute(stmt)).scalars().first()
            return table_session_to_domain(row) if row is not None else None

    async def list_open(self, tenant_id: str) -> list[TableSession]:
        async with self._session_factory() as session:
            stmt = (
                select(TableSessionORM)
                .where(
                    TableSessionORM.tenant_id == tenant_id,
                    TableSessionORM.closed_at.is_(None),
                    TableSessionORM.merged_into_id.is_(None),
                )
                .order_by(TableSessionORM.opened_at.asc())
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [table_session_to_domain(row) for row in rows]

    async def add(self, table_session: TableSession) -> None:
        async with self._session_factory() as session:
            session.add(table_session_to_orm(table_session))

    async def save(self, table_session: TableSession) -> None:
        async with self._session_factory() as session:
            await session.merge(table_session_to_orm(table_session))
