"""Food-cost read model (CQRS-lite): per product with a recipe, its food cost
(Σ insumos × costo), price, gross margin and food-cost ratio. Behind a port so
the use case stays free of SQLAlchemy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.identity.ports import TenantContext


@dataclass(frozen=True)
class FoodCostRow:
    product_id: str
    product_name: str
    price_amount: int
    food_cost_amount: int
    margin_amount: int  # price − food cost; may be negative (sold below cost)
    food_cost_ratio_bps: int  # food cost / price, in basis points
    currency: str


@dataclass(frozen=True)
class FoodCostReport:
    currency: str
    rows: list[FoodCostRow]


class FoodCostReadModel(ABC):
    @abstractmethod
    async def food_cost(self, tenant_id: str) -> FoodCostReport: ...


class GetFoodCost:
    def __init__(
        self, read_model: FoodCostReadModel, tenant_context: TenantContext
    ) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> FoodCostReport:
        self._tenant_context.set(tenant_id)
        return await self._read_model.food_cost(tenant_id)
