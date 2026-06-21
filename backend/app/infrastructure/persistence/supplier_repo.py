from __future__ import annotations

from sqlalchemy import select

from app.domain.inventory.entities import Supplier
from app.domain.inventory.repository import SupplierRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import supplier_to_domain, supplier_to_orm
from app.infrastructure.persistence.models import SupplierORM


class SqlAlchemySupplierRepository(SupplierRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, tenant_id: str, supplier_id: str) -> Supplier | None:
        async with self._session_factory() as session:
            stmt = select(SupplierORM).where(
                SupplierORM.id == supplier_id, SupplierORM.tenant_id == tenant_id
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return supplier_to_domain(row) if row is not None else None

    async def list(self, tenant_id: str, *, active_only: bool = False) -> list[Supplier]:
        async with self._session_factory() as session:
            stmt = select(SupplierORM).where(SupplierORM.tenant_id == tenant_id)
            if active_only:
                stmt = stmt.where(SupplierORM.active.is_(True))
            stmt = stmt.order_by(SupplierORM.name)
            rows = (await session.execute(stmt)).scalars().all()
            return [supplier_to_domain(row) for row in rows]

    async def add(self, supplier: Supplier) -> None:
        async with self._session_factory() as session:
            session.add(supplier_to_orm(supplier))

    async def save(self, supplier: Supplier) -> None:
        async with self._session_factory() as session:
            await session.merge(supplier_to_orm(supplier))
