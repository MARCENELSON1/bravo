from __future__ import annotations

from sqlalchemy import delete, select

from app.domain.table_session.entities import Sector
from app.domain.table_session.repository import SectorRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import sector_to_domain, sector_to_orm
from app.infrastructure.persistence.models import SectorORM


class SqlAlchemySectorRepository(SectorRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS).
    Sectors are ordered by ``sort_order`` then name (what the floor renders)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, tenant_id: str, sector_id: str) -> Sector | None:
        async with self._session_factory() as session:
            stmt = select(SectorORM).where(
                SectorORM.id == sector_id, SectorORM.tenant_id == tenant_id
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return sector_to_domain(row) if row is not None else None

    async def list(self, tenant_id: str) -> list[Sector]:
        async with self._session_factory() as session:
            stmt = (
                select(SectorORM)
                .where(SectorORM.tenant_id == tenant_id)
                .order_by(SectorORM.sort_order, SectorORM.name)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [sector_to_domain(row) for row in rows]

    async def add(self, sector: Sector) -> None:
        async with self._session_factory() as session:
            session.add(sector_to_orm(sector))

    async def save(self, sector: Sector) -> None:
        async with self._session_factory() as session:
            await session.merge(sector_to_orm(sector))

    async def delete(self, tenant_id: str, sector_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                delete(SectorORM).where(
                    SectorORM.id == sector_id, SectorORM.tenant_id == tenant_id
                )
            )
