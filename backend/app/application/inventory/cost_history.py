"""Ingredient cost history read model (Fase 2D, T1.4): the purchase-price trail
of an ingredient over time, from the already-captured stock_movements (no new
table). The current ``Ingredient.unit_cost`` is the last purchase = replacement
cost; this exposes how it got there. Behind a port so the use case stays free of
SQLAlchemy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.identity.ports import TenantContext


@dataclass(frozen=True)
class IngredientCostPoint:
    occurred_at: str  # ISO — when the purchase was registered
    unit_cost_amount: int  # cost per base unit at that purchase
    currency: str


class IngredientCostHistoryReadModel(ABC):
    @abstractmethod
    async def history(
        self, tenant_id: str, ingredient_id: str
    ) -> list[IngredientCostPoint]: ...


class GetIngredientCostHistory:
    def __init__(
        self,
        read_model: IngredientCostHistoryReadModel,
        tenant_context: TenantContext,
    ) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, ingredient_id: str
    ) -> list[IngredientCostPoint]:
        self._tenant_context.set(tenant_id)
        return await self._read_model.history(tenant_id, ingredient_id)
