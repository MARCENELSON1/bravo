from __future__ import annotations

from sqlalchemy import select

from app.domain.tenant.entities import Tenant
from app.domain.tenant.repository import TenantRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import tenant_to_domain, tenant_to_orm
from app.infrastructure.persistence.models import TenantORM


class SqlAlchemyTenantRepository(TenantRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, tenant_id: str) -> Tenant | None:
        async with self._session_factory() as session:
            row = await session.get(TenantORM, tenant_id)
            return tenant_to_domain(row) if row is not None else None

    async def get_by_slug(self, slug: str) -> Tenant | None:
        async with self._session_factory() as session:
            stmt = select(TenantORM).where(TenantORM.slug == slug)
            row = (await session.execute(stmt)).scalar_one_or_none()
            return tenant_to_domain(row) if row is not None else None

    async def add(self, tenant: Tenant) -> None:
        async with self._session_factory() as session:
            session.add(tenant_to_orm(tenant))
