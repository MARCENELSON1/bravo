"""Gold read models over the canonical model (sale_facts) + payments. Computed
in SQL; tenant-scoped (RLS + explicit filter); read-only. The three read models
live together because they share the same sources and period semantics."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select

from app.application.analytics.read_models import (
    PaymentMixReadModel,
    PaymentMixRow,
    ProductPerformanceReadModel,
    ProductPerformanceRow,
    RevenueReadModel,
    RevenueSummary,
)
from app.domain.payment.value_objects import PaymentDirection, PaymentStatus
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import PaymentORM, SaleFactORM, TenantORM


async def _tenant_currency(session, tenant_id: str) -> str:
    currency = (
        await session.execute(select(TenantORM.currency).where(TenantORM.id == tenant_id))
    ).scalar_one_or_none()
    return currency if currency is not None else "ARS"


class SqlAlchemyRevenueReadModel(RevenueReadModel):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def summary(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> RevenueSummary:
        async with self._session_factory() as session:
            currency = await _tenant_currency(session, tenant_id)

            sales_stmt = select(
                func.coalesce(func.sum(SaleFactORM.line_amount), 0),
                func.coalesce(func.sum(SaleFactORM.food_cost_amount), 0),
                func.count(func.distinct(SaleFactORM.order_id)),
            ).where(SaleFactORM.tenant_id == tenant_id)
            if since is not None:
                sales_stmt = sales_stmt.where(SaleFactORM.occurred_at >= since)
            if until is not None:
                sales_stmt = sales_stmt.where(SaleFactORM.occurred_at <= until)
            sales_amount, food_cost_amount, orders_count = (
                await session.execute(sales_stmt)
            ).one()

            collected = await self._payment_total(
                session, tenant_id, PaymentDirection.INFLOW, since, until
            )
            expense = await self._payment_total(
                session, tenant_id, PaymentDirection.OUTFLOW, since, until
            )

            sales_amount = int(sales_amount)
            food_cost_amount = int(food_cost_amount)
            orders_count = int(orders_count)
            return RevenueSummary(
                currency=currency,
                sales_amount=sales_amount,
                collected_amount=collected,
                expense_amount=expense,
                food_cost_amount=food_cost_amount,
                gross_margin_amount=sales_amount - food_cost_amount,
                orders_count=orders_count,
                average_ticket_amount=sales_amount // orders_count if orders_count else 0,
            )

    @staticmethod
    async def _payment_total(
        session,
        tenant_id: str,
        direction: PaymentDirection,
        since: datetime | None,
        until: datetime | None,
    ) -> int:
        stmt = select(func.coalesce(func.sum(PaymentORM.amount), 0)).where(
            PaymentORM.tenant_id == tenant_id,
            PaymentORM.direction == direction.value,
            PaymentORM.status == PaymentStatus.CONFIRMED.value,
        )
        if since is not None:
            stmt = stmt.where(PaymentORM.created_at >= since)
        if until is not None:
            stmt = stmt.where(PaymentORM.created_at <= until)
        return int((await session.execute(stmt)).scalar_one())


class SqlAlchemyPaymentMixReadModel(PaymentMixReadModel):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def mix(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[PaymentMixRow]:
        async with self._session_factory() as session:
            amount = func.coalesce(func.sum(PaymentORM.amount), 0)
            stmt = (
                select(PaymentORM.method, PaymentORM.direction, amount, func.count())
                .where(
                    PaymentORM.tenant_id == tenant_id,
                    PaymentORM.status == PaymentStatus.CONFIRMED.value,
                )
                .group_by(PaymentORM.method, PaymentORM.direction)
                .order_by(amount.desc())
            )
            if since is not None:
                stmt = stmt.where(PaymentORM.created_at >= since)
            if until is not None:
                stmt = stmt.where(PaymentORM.created_at <= until)
            return [
                PaymentMixRow(
                    method=method, direction=direction, amount=int(total), count=int(count)
                )
                for method, direction, total, count in (await session.execute(stmt)).all()
            ]


class SqlAlchemyProductPerformanceReadModel(ProductPerformanceReadModel):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def top(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 10,
    ) -> list[ProductPerformanceRow]:
        async with self._session_factory() as session:
            currency = await _tenant_currency(session, tenant_id)
            sales = func.coalesce(func.sum(SaleFactORM.line_amount), 0)
            food_cost = func.coalesce(func.sum(SaleFactORM.food_cost_amount), 0)
            stmt = (
                select(
                    SaleFactORM.product_id,
                    SaleFactORM.product_name,
                    func.coalesce(func.sum(SaleFactORM.quantity), 0),
                    sales,
                    food_cost,
                )
                .where(SaleFactORM.tenant_id == tenant_id)
                .group_by(SaleFactORM.product_id, SaleFactORM.product_name)
                .order_by(sales.desc())
                .limit(limit)
            )
            if since is not None:
                stmt = stmt.where(SaleFactORM.occurred_at >= since)
            if until is not None:
                stmt = stmt.where(SaleFactORM.occurred_at <= until)
            rows: list[ProductPerformanceRow] = []
            for product_id, name, units, sales_amount, food_cost_amount in (
                await session.execute(stmt)
            ).all():
                sales_amount = int(sales_amount)
                food_cost_amount = int(food_cost_amount)
                rows.append(
                    ProductPerformanceRow(
                        product_id=product_id,
                        product_name=name,
                        units_sold=int(units),
                        sales_amount=sales_amount,
                        food_cost_amount=food_cost_amount,
                        margin_amount=sales_amount - food_cost_amount,
                        currency=currency,
                    )
                )
            return rows
