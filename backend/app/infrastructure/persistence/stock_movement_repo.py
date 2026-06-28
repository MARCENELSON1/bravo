from __future__ import annotations

from sqlalchemy import delete, select

from app.domain.inventory.entities import StockMovement
from app.domain.inventory.repository import StockMovementRepository
from app.domain.inventory.value_objects import MovementReason
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    stock_movement_to_domain,
    stock_movement_to_orm,
)
from app.infrastructure.persistence.models import StockMovementORM


class SqlAlchemyStockMovementRepository(StockMovementRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def add(self, movement: StockMovement) -> None:
        async with self._session_factory() as session:
            session.add(stock_movement_to_orm(movement))

    async def exists_for_order(self, tenant_id: str, order_id: str) -> bool:
        """True once an order has been consumed (a SALE movement exists) — the
        idempotency guard so a re-settle never discounts stock twice."""
        async with self._session_factory() as session:
            stmt = (
                select(StockMovementORM.id)
                .where(
                    StockMovementORM.tenant_id == tenant_id,
                    StockMovementORM.order_id == order_id,
                    StockMovementORM.reason == MovementReason.SALE.value,
                )
                .limit(1)
            )
            return (await session.execute(stmt)).first() is not None

    async def list_sales_for_order(
        self, tenant_id: str, order_id: str
    ) -> list[StockMovement]:
        """The SALE movements an order discounted — what a reopen credits back."""
        async with self._session_factory() as session:
            stmt = select(StockMovementORM).where(
                StockMovementORM.tenant_id == tenant_id,
                StockMovementORM.order_id == order_id,
                StockMovementORM.reason == MovementReason.SALE.value,
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [stock_movement_to_domain(row) for row in rows]

    async def delete_sales_for_order(self, tenant_id: str, order_id: str) -> None:
        """Drop an order's SALE movements on a reopen, so the idempotency guard
        resets and a re-pay re-consumes from scratch."""
        async with self._session_factory() as session:
            await session.execute(
                delete(StockMovementORM).where(
                    StockMovementORM.tenant_id == tenant_id,
                    StockMovementORM.order_id == order_id,
                    StockMovementORM.reason == MovementReason.SALE.value,
                )
            )

    async def list_for_ingredient(
        self, tenant_id: str, ingredient_id: str
    ) -> list[StockMovement]:
        async with self._session_factory() as session:
            stmt = (
                select(StockMovementORM)
                .where(
                    StockMovementORM.tenant_id == tenant_id,
                    StockMovementORM.ingredient_id == ingredient_id,
                )
                .order_by(StockMovementORM.created_at.desc())
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [stock_movement_to_domain(row) for row in rows]
