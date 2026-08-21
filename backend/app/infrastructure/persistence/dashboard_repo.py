from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select

from app.application.reporting.dashboard import DashboardReadModel, DashboardSummary
from app.domain.order.value_objects import OrderStatus
from app.domain.payment.value_objects import PaymentDirection, PaymentStatus
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import OrderORM, PaymentORM, TenantORM
from app.infrastructure.persistence.payment_columns import net_collected_col

_FINAL = (OrderStatus.PAID.value, OrderStatus.CANCELLED.value)


class SqlAlchemyDashboardReadModel(DashboardReadModel):
    """Aggregations over the tenant's payments + orders. Tenant-scoped (RLS +
    explicit filter); read-only, so it bypasses the domain repositories."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def summary(
        self,
        tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> DashboardSummary:
        async with self._session_factory() as session:
            currency = (
                await session.execute(select(TenantORM.currency).where(TenantORM.id == tenant_id))
            ).scalar_one_or_none() or "ARS"

            # Ventana por fecha de cobro (mismo predicado que payment-mix → el hero
            # cuadra exacto con "Cobros por canal"). Sin since/until → all-time.
            def _windowed(stmt):
                if since is not None:
                    stmt = stmt.where(PaymentORM.created_at >= since)
                if until is not None:
                    stmt = stmt.where(PaymentORM.created_at <= until)
                return stmt

            sales, payment_count, collected_net, fees_total = (
                await session.execute(
                    _windowed(
                        select(
                            func.coalesce(func.sum(PaymentORM.amount), 0),
                            func.count(),
                            func.coalesce(func.sum(net_collected_col()), 0),
                            func.coalesce(func.sum(PaymentORM.fee_amount), 0),
                        ).where(
                            PaymentORM.tenant_id == tenant_id,
                            PaymentORM.direction == PaymentDirection.INFLOW.value,
                            PaymentORM.status == PaymentStatus.CONFIRMED.value,
                        )
                    )
                )
            ).one()

            expenses = (
                await session.execute(
                    _windowed(
                        select(func.coalesce(func.sum(PaymentORM.amount), 0)).where(
                            PaymentORM.tenant_id == tenant_id,
                            PaymentORM.direction == PaymentDirection.OUTFLOW.value,
                            PaymentORM.status == PaymentStatus.CONFIRMED.value,
                        )
                    )
                )
            ).scalar_one()

            active = (
                await session.execute(
                    select(func.count()).where(
                        OrderORM.tenant_id == tenant_id, OrderORM.status.notin_(_FINAL)
                    )
                )
            ).scalar_one()

            paid = (
                await session.execute(
                    select(func.count()).where(
                        OrderORM.tenant_id == tenant_id,
                        OrderORM.status == OrderStatus.PAID.value,
                    )
                )
            ).scalar_one()

            sales, expenses, active, paid = int(sales), int(expenses), int(active), int(paid)
            return DashboardSummary(
                currency=currency,
                sales=sales,
                expenses=expenses,
                net=sales - expenses,
                active_orders=active,
                paid_orders=paid,
                avg_ticket=sales // paid if paid > 0 else 0,
                payment_count=int(payment_count),
                collected_net=int(collected_net),
                fees_total=int(fees_total),
            )
