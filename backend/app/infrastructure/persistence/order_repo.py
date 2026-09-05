from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.order.entities import Order
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import ItemStatus, OrderSource, OrderStatus, Station
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    order_item_to_orm,
    order_to_domain,
    order_to_orm,
)
from app.infrastructure.persistence.models import OrderItemORM, OrderORM

# The KDS shows orders that have at least one item still being made.
# HELD también: la cocina ve el curso que viene (mise en place) aunque no lo cocine.
_KDS_ITEM_STATUSES = (
    ItemStatus.HELD.value,
    ItemStatus.SENT.value,
    ItemStatus.PREPARING.value,
)
_ACTIVE_STATUSES = (
    OrderStatus.OPEN.value,
    OrderStatus.SENT.value,
    OrderStatus.PREPARING.value,
    OrderStatus.READY.value,
    OrderStatus.SERVED.value,
)


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

    async def _load_many(
        self, session: AsyncSession, rows: Sequence[OrderORM], tenant_id: str
    ) -> list[Order]:
        """Hydrate a list of orders with **two** queries instead of one per order.

        There is no mapped ``relationship()`` between orders and their items
        (the aggregate is assembled by hand in ``mappers.py``), so the items of
        every order come back in a single ``IN`` query and are grouped in
        memory. The hot lists (floor, KDS) used to issue one query per order,
        which each connected device paid on every poll.
        """
        if not rows:
            return []  # an empty IN () is invalid SQL
        items_by_order: dict[str, list[OrderItemORM]] = {row.id: [] for row in rows}
        item_rows = (
            await session.execute(
                select(OrderItemORM)
                .where(
                    OrderItemORM.order_id.in_(items_by_order.keys()),
                    OrderItemORM.tenant_id == tenant_id,
                )
                .order_by(OrderItemORM.position)  # keeps each order's line order
            )
        ).scalars().all()
        for item in item_rows:
            items_by_order[item.order_id].append(item)
        return [order_to_domain(row, items_by_order[row.id]) for row in rows]

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
            return await self._load_many(session, rows, tenant_id)

    async def list_kds(
        self, tenant_id: str, station: Station | None = None
    ) -> list[Order]:
        async with self._session_factory() as session:
            item_conds = [
                OrderItemORM.order_id == OrderORM.id,
                OrderItemORM.tenant_id == tenant_id,
                OrderItemORM.status.in_(_KDS_ITEM_STATUSES),
            ]
            if station is not None:
                item_conds.append(OrderItemORM.station == station.value)
            has_active_item = select(OrderItemORM.id).where(*item_conds).exists()
            stmt = (
                select(OrderORM)
                .where(OrderORM.tenant_id == tenant_id, has_active_item)
                .order_by(OrderORM.created_at.asc())
            )
            rows = (await session.execute(stmt)).scalars().all()
            return await self._load_many(session, rows, tenant_id)

    async def list_active(self, tenant_id: str) -> list[Order]:
        async with self._session_factory() as session:
            stmt = (
                select(OrderORM)
                .where(
                    OrderORM.tenant_id == tenant_id,
                    OrderORM.status.in_(_ACTIVE_STATUSES),
                )
                .order_by(OrderORM.created_at.asc())
            )
            rows = (await session.execute(stmt)).scalars().all()
            return await self._load_many(session, rows, tenant_id)

    async def list_open_by_session(
        self, tenant_id: str, session_id: str
    ) -> list[Order]:
        async with self._session_factory() as session:
            stmt = (
                select(OrderORM)
                .where(
                    OrderORM.tenant_id == tenant_id,
                    OrderORM.session_id == session_id,
                    OrderORM.status.in_(_ACTIVE_STATUSES),
                )
                .order_by(OrderORM.created_at.asc())
            )
            rows = (await session.execute(stmt)).scalars().all()
            return await self._load_many(session, rows, tenant_id)

    async def list_pending_qr(self, tenant_id: str) -> list[Order]:
        async with self._session_factory() as session:
            stmt = (
                select(OrderORM)
                .where(
                    OrderORM.tenant_id == tenant_id,
                    OrderORM.status == OrderStatus.OPEN.value,
                    OrderORM.source == OrderSource.CUSTOMER_QR.value,
                )
                .order_by(OrderORM.created_at.asc())
            )
            rows = (await session.execute(stmt)).scalars().all()
            return await self._load_many(session, rows, tenant_id)

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
