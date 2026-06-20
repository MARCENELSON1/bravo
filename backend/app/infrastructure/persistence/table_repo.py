from __future__ import annotations

from sqlalchemy import select

from app.domain.table.entities import Table
from app.domain.table.repository import TableRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import table_to_domain, table_to_orm
from app.infrastructure.persistence.models import TableORM


class SqlAlchemyTableRepository(TableRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, tenant_id: str, table_id: str) -> Table | None:
        async with self._session_factory() as session:
            stmt = select(TableORM).where(
                TableORM.id == table_id, TableORM.tenant_id == tenant_id
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return table_to_domain(row) if row is not None else None

    async def list(self, tenant_id: str) -> list[Table]:
        async with self._session_factory() as session:
            stmt = (
                select(TableORM)
                .where(TableORM.tenant_id == tenant_id)
                .order_by(TableORM.number)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [table_to_domain(row) for row in rows]

    async def add(self, table: Table) -> None:
        async with self._session_factory() as session:
            session.add(table_to_orm(table))

    async def save(self, table: Table) -> None:
        async with self._session_factory() as session:
            await session.merge(table_to_orm(table))
