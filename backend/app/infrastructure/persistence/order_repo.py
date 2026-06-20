from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.order.entities import Order
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import OrderStatus
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    order_item_to_orm,
    order_to_domain,
    order_to_orm,
)
from app.infrastructure.persistence.models import OrderItemORM, OrderORM

_KDS_STATUSES = (OrderStatus.SENT.value, OrderStatus.PREPARING.value)


class SqlAlchemyOrderRepository(OrderRepository):
    """Aggregate repo (order + items). Every query is scoped by ``tenant_id``."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def _load(self, session: AsyncSession, row: OrderORM) -> Order:
        items = (
            await session.execute(
                select(OrderItemORM)
                .where(OrderItemORM.order_id == row.id, OrderItemORM.tenant_id == row.tenant_id)
                .order_by(OrderItemORM.position)
            )
        ).scalars().all()
        return order_to_domain(row, list(items))

    async def get_by_id(self, tenant_id: str, order_id: str) -> Order | None:
        async with self._session_factory() as session:
            row = (
                await session.execute(
                    select(OrderORM).where(
                        OrderORM.id == order_id, OrderORM.tenant_id == tenant_id
                    )
                )
            ).scalar_one_or_none()
            return await self._load(session, row) if row is not None else None

    async def list_by_status(
        self, tenant_id: str, status: OrderStatus | None = None
    ) -> list[Order]:
        async with self._session_factory() as session:
            stmt = select(OrderORM).where(OrderORM.tenant_id == tenant_id)
            if status is not None:
                stmt = stmt.where(OrderORM.status == status.value)
            stmt = stmt.order_by(OrderORM.created_at.desc())
            rows = (await session.execute(stmt)).scalars().all()
            return [await self._load(session, row) for row in rows]

    async def list_kds(self, tenant_id: str) -> list[Order]:
        async with self._session_factory() as session:
            stmt = (
                select(OrderORM)
                .where(OrderORM.tenant_id == tenant_id, OrderORM.status.in_(_KDS_STATUSES))
                .order_by(OrderORM.created_at.asc())
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [await self._load(session, row) for row in rows]

    async def add(self, order: Order) -> None:
        async with self._session_factory() as session:
            session.add(order_to_orm(order))
            for position, item in enumerate(order.items):
                session.add(order_item_to_orm(item, order, position))

    async def save(self, order: Order) -> None:
        async with self._session_factory() as session:
            await session.merge(order_to_orm(order))
            await session.execute(
                delete(OrderItemORM).where(
                    OrderItemORM.order_id == order.id,
                    OrderItemORM.tenant_id == order.tenant_id,
                )
            )
            for position, item in enumerate(order.items):
                session.add(order_item_to_orm(item, order, position))
