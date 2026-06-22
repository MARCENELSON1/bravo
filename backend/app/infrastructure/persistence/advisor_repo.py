"""Advisor read model: raw canonical metrics for a period (sales/food cost from
sale_facts, mermas from stock_movements×ingredients, no-show rate from
reservations). Tenant-scoped (RLS + filter); read-only."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select

from app.application.advisor.report import AdvisorMetrics, AdvisorReadModel
from app.domain.advisor.kpis import ratio_bps
from app.domain.inventory.value_objects import MovementReason
from app.domain.reservation.value_objects import ReservationStatus
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import (
    IngredientORM,
    ReservationORM,
    SaleFactORM,
    StockMovementORM,
    TenantORM,
)

_QUANTITY_SCALE = 1000


class SqlAlchemyAdvisorReadModel(AdvisorReadModel):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def metrics(
        self, tenant_id: str, since: datetime, until: datetime
    ) -> AdvisorMetrics:
        async with self._session_factory() as session:
            currency = (
                await session.execute(
                    select(TenantORM.currency).where(TenantORM.id == tenant_id)
                )
            ).scalar_one_or_none() or "ARS"

            sales, food_cost, orders = (
                await session.execute(
                    select(
                        func.coalesce(func.sum(SaleFactORM.line_amount), 0),
                        func.coalesce(func.sum(SaleFactORM.food_cost_amount), 0),
                        func.count(func.distinct(SaleFactORM.order_id)),
                    ).where(
                        SaleFactORM.tenant_id == tenant_id,
                        SaleFactORM.occurred_at >= since,
                        SaleFactORM.occurred_at <= until,
                    )
                )
            ).one()

            # Mermas valorizadas: qty (milésimas) × unit_cost / 1000.
            waste_raw = (
                await session.execute(
                    select(
                        func.coalesce(
                            func.sum(StockMovementORM.qty * IngredientORM.unit_cost_amount),
                            0,
                        )
                    )
                    .select_from(StockMovementORM)
                    .join(IngredientORM, IngredientORM.id == StockMovementORM.ingredient_id)
                    .where(
                        StockMovementORM.tenant_id == tenant_id,
                        StockMovementORM.reason == MovementReason.WASTE.value,
                        StockMovementORM.created_at >= since,
                        StockMovementORM.created_at <= until,
                    )
                )
            ).scalar_one()
            waste_amount = int(waste_raw) // _QUANTITY_SCALE

            counts = {
                status: int(count)
                for status, count in (
                    await session.execute(
                        select(ReservationORM.status, func.count())
                        .where(
                            ReservationORM.tenant_id == tenant_id,
                            ReservationORM.reserved_at >= since,
                            ReservationORM.reserved_at <= until,
                        )
                        .group_by(ReservationORM.status)
                    )
                ).all()
            }
            no_shows = counts.get(ReservationStatus.NO_SHOW.value, 0)
            shows = (
                no_shows
                + counts.get(ReservationStatus.COMPLETED.value, 0)
                + counts.get(ReservationStatus.SEATED.value, 0)
            )

            return AdvisorMetrics(
                currency=currency,
                sales_amount=int(sales),
                food_cost_amount=int(food_cost),
                orders_count=int(orders),
                waste_amount=waste_amount,
                no_show_rate_bps=ratio_bps(no_shows, shows),
            )
