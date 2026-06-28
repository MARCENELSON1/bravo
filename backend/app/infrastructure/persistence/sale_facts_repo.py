from __future__ import annotations

from sqlalchemy import delete, select

from app.application.analytics.facts import SaleFact
from app.application.analytics.ports import SaleFactsRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import SaleFactORM


def _to_domain(row: SaleFactORM) -> SaleFact:
    return SaleFact(
        id=row.id,
        tenant_id=row.tenant_id,
        order_id=row.order_id,
        order_item_id=row.order_item_id,
        product_id=row.product_id,
        product_name=row.product_name,
        category=row.category,
        quantity=row.quantity,
        unit_price_amount=row.unit_price_amount,
        line_amount=row.line_amount,
        food_cost_amount=row.food_cost_amount,
        currency=row.currency,
        waiter_id=row.waiter_id,
        table_id=row.table_id,
        occurred_at=row.occurred_at,
        created_at=row.created_at,
    )


def _to_orm(fact: SaleFact) -> SaleFactORM:
    return SaleFactORM(
        id=fact.id,
        tenant_id=fact.tenant_id,
        order_id=fact.order_id,
        order_item_id=fact.order_item_id,
        product_id=fact.product_id,
        product_name=fact.product_name,
        category=fact.category,
        quantity=fact.quantity,
        unit_price_amount=fact.unit_price_amount,
        line_amount=fact.line_amount,
        food_cost_amount=fact.food_cost_amount,
        currency=fact.currency,
        waiter_id=fact.waiter_id,
        table_id=fact.table_id,
        occurred_at=fact.occurred_at,
    )


class SqlAlchemySaleFactsRepository(SaleFactsRepository):
    """Write side of the canonical sale_facts. Scoped by ``tenant_id``."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def exists_for_order(self, tenant_id: str, order_id: str) -> bool:
        async with self._session_factory() as session:
            stmt = (
                select(SaleFactORM.id)
                .where(SaleFactORM.tenant_id == tenant_id, SaleFactORM.order_id == order_id)
                .limit(1)
            )
            return (await session.execute(stmt)).first() is not None

    async def add_many(self, facts: list[SaleFact]) -> None:
        if not facts:
            return
        async with self._session_factory() as session:
            session.add_all([_to_orm(fact) for fact in facts])

    async def list_for_order(self, tenant_id: str, order_id: str) -> list[SaleFact]:
        async with self._session_factory() as session:
            stmt = select(SaleFactORM).where(
                SaleFactORM.tenant_id == tenant_id, SaleFactORM.order_id == order_id
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_domain(row) for row in rows]

    async def delete_for_order(self, tenant_id: str, order_id: str) -> None:
        """Remove the order's facts on a reopen — the inverse of ``add_many``."""
        async with self._session_factory() as session:
            await session.execute(
                delete(SaleFactORM).where(
                    SaleFactORM.tenant_id == tenant_id,
                    SaleFactORM.order_id == order_id,
                )
            )
