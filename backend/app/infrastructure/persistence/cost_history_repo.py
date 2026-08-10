"""Ingredient cost history (Fase 2D, T1.4): the ascending purchase-price trail
from stock_movements (reason=PURCHASE). Tenant-scoped (RLS + explicit filter);
read-only. No new table — reuses the unit_cost already frozen per purchase."""

from __future__ import annotations

from sqlalchemy import select

from app.application.inventory.cost_history import (
    IngredientCostHistoryReadModel,
    IngredientCostPoint,
)
from app.domain.inventory.value_objects import MovementReason
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import StockMovementORM


class SqlAlchemyIngredientCostHistoryReadModel(IngredientCostHistoryReadModel):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def history(
        self, tenant_id: str, ingredient_id: str
    ) -> list[IngredientCostPoint]:
        async with self._session_factory() as session:
            rows = (
                await session.execute(
                    select(
                        StockMovementORM.created_at,
                        StockMovementORM.unit_cost_amount,
                        StockMovementORM.unit_cost_currency,
                    )
                    .where(
                        StockMovementORM.tenant_id == tenant_id,
                        StockMovementORM.ingredient_id == ingredient_id,
                        StockMovementORM.reason == MovementReason.PURCHASE.value,
                        StockMovementORM.unit_cost_amount.is_not(None),
                    )
                    .order_by(StockMovementORM.created_at.asc())
                )
            ).all()
            return [
                IngredientCostPoint(
                    occurred_at=created_at.isoformat(),
                    unit_cost_amount=int(amount),
                    currency=currency or "ARS",
                )
                for created_at, amount, currency in rows
            ]
