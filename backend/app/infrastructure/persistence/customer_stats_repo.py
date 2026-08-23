from __future__ import annotations

from sqlalchemy import distinct, func, select

from app.application.customer.use_cases import (
    CustomerStats,
    CustomerStatsReadModel,
    CustomerStatsReport,
)
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import (
    CustomerORM,
    OrderORM,
    SaleFactORM,
    TenantORM,
)


class SqlAlchemyCustomerStatsReadModel(CustomerStatsReadModel):
    """Per-customer aggregates over attributed sales (customers LEFT JOIN
    orders→sale_facts), so customers with no attributed orders come back with
    zeros. Tenant-scoped; read-only."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def list_stats(self, tenant_id: str) -> CustomerStatsReport:
        async with self._session_factory() as db:
            currency = (
                await db.execute(
                    select(TenantORM.currency).where(TenantORM.id == tenant_id)
                )
            ).scalar_one_or_none() or "ARS"

            rows = (
                await db.execute(
                    select(
                        CustomerORM.id,
                        CustomerORM.name,
                        CustomerORM.phone,
                        func.count(distinct(SaleFactORM.order_id)),
                        func.coalesce(func.sum(SaleFactORM.line_amount), 0),
                        func.min(SaleFactORM.occurred_at),
                        func.max(SaleFactORM.occurred_at),
                    )
                    .select_from(CustomerORM)
                    .join(
                        OrderORM,
                        (OrderORM.customer_id == CustomerORM.id)
                        & (OrderORM.tenant_id == tenant_id),
                        isouter=True,
                    )
                    .join(
                        SaleFactORM,
                        (SaleFactORM.order_id == OrderORM.id)
                        & (SaleFactORM.tenant_id == tenant_id),
                        isouter=True,
                    )
                    .where(CustomerORM.tenant_id == tenant_id)
                    .group_by(CustomerORM.id, CustomerORM.name, CustomerORM.phone)
                    .order_by(CustomerORM.name)
                )
            ).all()

        return CustomerStatsReport(
            currency=currency,
            rows=[
                CustomerStats(
                    customer_id=cid,
                    name=name,
                    phone=phone,
                    visits=int(visits),
                    total_spent=int(total),
                    first_visit_at=first,
                    last_visit_at=last,
                )
                for cid, name, phone, visits, total, first, last in rows
            ],
        )
