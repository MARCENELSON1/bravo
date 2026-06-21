"""Dashboard summary read model (CQRS-lite): a thin read-side over payments +
orders, behind a port so the use case stays free of SQLAlchemy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.identity.ports import TenantContext


@dataclass(frozen=True)
class DashboardSummary:
    currency: str
    sales: int  # confirmed INFLOW total (minor units)
    expenses: int  # confirmed OUTFLOW total (minor units)
    net: int  # sales − expenses
    active_orders: int  # not PAID/CANCELLED
    paid_orders: int
    avg_ticket: int  # sales / paid_orders (0 if none)
    payment_count: int  # confirmed inflow payments


class DashboardReadModel(ABC):
    @abstractmethod
    async def summary(self, tenant_id: str) -> DashboardSummary: ...


class GetDashboardSummary:
    def __init__(self, read_model: DashboardReadModel, tenant_context: TenantContext) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> DashboardSummary:
        self._tenant_context.set(tenant_id)
        return await self._read_model.summary(tenant_id)
