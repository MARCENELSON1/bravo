"""Gold read models (KPIs) over the canonical model. Behind ports so the use
cases (and the advisor/copiloto later) stay free of SQLAlchemy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class RevenueSummary:
    currency: str
    sales_amount: int  # accrual: Σ sale_facts.line_amount (lo vendido)
    collected_amount: int  # cash: Σ pagos INFLOW confirmados (lo cobrado)
    expense_amount: int  # Σ pagos OUTFLOW confirmados (egresos)
    food_cost_amount: int  # Σ sale_facts.food_cost (COGS de recetas)
    gross_margin_amount: int  # sales − food_cost (puede ser negativo)
    orders_count: int  # comandas PAID proyectadas en el período
    average_ticket_amount: int  # sales / orders (0 si no hay)


@dataclass(frozen=True)
class PaymentMixRow:
    method: str
    direction: str
    amount: int
    count: int


@dataclass(frozen=True)
class ProductPerformanceRow:
    product_id: str
    product_name: str
    units_sold: int
    sales_amount: int
    food_cost_amount: int
    margin_amount: int  # sales − food_cost (puede ser negativo)
    currency: str


@dataclass(frozen=True)
class RevenueDailyPoint:
    """Un día de facturación (accrual). Días sin ventas NO vienen — el consumidor
    rellena con ceros. El corte de día es en UTC (MVP; ver plan Identidad Wellnod)."""

    day: date
    sales_amount: int  # Σ sale_facts.line_amount del día
    orders_count: int  # comandas distintas proyectadas ese día


class RevenueReadModel(ABC):
    @abstractmethod
    async def summary(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> RevenueSummary: ...


class RevenueDailyReadModel(ABC):
    @abstractmethod
    async def daily(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[RevenueDailyPoint]: ...


class PaymentMixReadModel(ABC):
    @abstractmethod
    async def mix(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[PaymentMixRow]: ...


class ProductPerformanceReadModel(ABC):
    @abstractmethod
    async def top(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 10,
    ) -> list[ProductPerformanceRow]: ...
