"""Escritura de los snapshots diarios (Tanda F). Upsert incremental (co-locado con
la proyección de sale_facts) + rebuild desde el historial canónico. Tenant-scoped."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, cast, delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.application.analytics.ports import (
    FinanceSnapshotRebuilder,
    FinanceSnapshotWriter,
)
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import FinanceDailySnapshotORM, SaleFactORM


class SqlAlchemyFinanceSnapshotRepository(FinanceSnapshotWriter, FinanceSnapshotRebuilder):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def add(
        self,
        tenant_id: str,
        day: date,
        *,
        sales_amount: int,
        food_cost_amount: int,
        orders_count: int,
        units_sold: int,
    ) -> None:
        """Upsert incremental: suma los deltas al día (negativos al revertir)."""
        async with self._session_factory() as session:
            stmt = pg_insert(FinanceDailySnapshotORM).values(
                tenant_id=tenant_id,
                day=day,
                sales_amount=sales_amount,
                food_cost_amount=food_cost_amount,
                orders_count=orders_count,
                units_sold=units_sold,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["tenant_id", "day"],
                set_={
                    "sales_amount": FinanceDailySnapshotORM.sales_amount + stmt.excluded.sales_amount,
                    "food_cost_amount": FinanceDailySnapshotORM.food_cost_amount
                    + stmt.excluded.food_cost_amount,
                    "orders_count": FinanceDailySnapshotORM.orders_count + stmt.excluded.orders_count,
                    "units_sold": FinanceDailySnapshotORM.units_sold + stmt.excluded.units_sold,
                },
            )
            await session.execute(stmt)

    async def rebuild(self, tenant_id: str) -> int:
        """Reconstruye todos los días desde sale_facts (borra + reinserta agrupado
        por día). Devuelve la cantidad de días reconstruidos."""
        day = cast(func.date_trunc("day", SaleFactORM.occurred_at), Date)
        async with self._session_factory() as session:
            await session.execute(
                delete(FinanceDailySnapshotORM).where(
                    FinanceDailySnapshotORM.tenant_id == tenant_id
                )
            )
            rows = (
                await session.execute(
                    select(
                        day,
                        func.coalesce(func.sum(SaleFactORM.line_amount), 0),
                        func.coalesce(func.sum(SaleFactORM.food_cost_amount), 0),
                        func.count(func.distinct(SaleFactORM.order_id)),
                        func.coalesce(func.sum(SaleFactORM.quantity), 0),
                    )
                    .where(SaleFactORM.tenant_id == tenant_id)
                    .group_by(day)
                )
            ).all()
            for bucket, sales, food, orders, units in rows:
                session.add(
                    FinanceDailySnapshotORM(
                        tenant_id=tenant_id,
                        day=bucket,
                        sales_amount=int(sales),
                        food_cost_amount=int(food),
                        orders_count=int(orders),
                        units_sold=int(units),
                    )
                )
            return len(rows)
