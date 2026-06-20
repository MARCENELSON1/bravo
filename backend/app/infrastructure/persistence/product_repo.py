from __future__ import annotations

from sqlalchemy import select

from app.domain.product.entities import Product
from app.domain.product.repository import ProductRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import product_to_domain, product_to_orm
from app.infrastructure.persistence.models import ProductORM


class SqlAlchemyProductRepository(ProductRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, tenant_id: str, product_id: str) -> Product | None:
        async with self._session_factory() as session:
            stmt = select(ProductORM).where(
                ProductORM.id == product_id, ProductORM.tenant_id == tenant_id
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return product_to_domain(row) if row is not None else None

    async def list(self, tenant_id: str, *, only_active: bool = False) -> list[Product]:
        async with self._session_factory() as session:
            stmt = select(ProductORM).where(ProductORM.tenant_id == tenant_id)
            if only_active:
                stmt = stmt.where(ProductORM.active.is_(True))
            stmt = stmt.order_by(ProductORM.name)
            rows = (await session.execute(stmt)).scalars().all()
            return [product_to_domain(row) for row in rows]

    async def add(self, product: Product) -> None:
        async with self._session_factory() as session:
            session.add(product_to_orm(product))

    async def save(self, product: Product) -> None:
        async with self._session_factory() as session:
            await session.merge(product_to_orm(product))
