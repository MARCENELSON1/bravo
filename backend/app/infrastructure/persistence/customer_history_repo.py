from __future__ import annotations

from sqlalchemy import distinct, func, select

from app.application.customer.use_cases import (
    CustomerHistory,
    CustomerHistoryReadModel,
)
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import OrderORM, SaleFactORM, TenantORM


class SqlAlchemyCustomerHistoryReadModel(CustomerHistoryReadModel):
    """A customer's spend over the sale_facts of orders attributed to them (join
    sale_facts → orders by ``customer_id``). Tenant-scoped; read-only."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def history(self, tenant_id: str, customer_id: str) -> CustomerHistory:
        async with self._session_factory() as db:
            currency = (
                await db.execute(
                    select(TenantORM.currency).where(TenantORM.id == tenant_id)
                )
            ).scalar_one_or_none() or "ARS"

            visits, total, last = (
                await db.execute(
                    select(
                        func.count(distinct(SaleFactORM.order_id)),
                        func.coalesce(func.sum(SaleFactORM.line_amount), 0),
                        func.max(SaleFactORM.occurred_at),
                    )
                    .select_from(SaleFactORM)
                    .join(OrderORM, OrderORM.id == SaleFactORM.order_id)
                    .where(
                        SaleFactORM.tenant_id == tenant_id,
                        OrderORM.customer_id == customer_id,
                    )
                )
            ).one()

        return CustomerHistory(
            customer_id=customer_id,
            currency=currency,
            visits=int(visits),
            total_spent=int(total),
            last_visit_at=last,
        )
