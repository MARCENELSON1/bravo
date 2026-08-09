from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.advisor.exceptions import InvalidAdvisorSettings
from app.domain.shared.exceptions import CurrencyMismatch
from app.domain.shared.money import Money


@dataclass
class AdvisorSettings:
    """Per-tenant cost profile (1:1). Drives the labor/prime cost, break-even and
    net margin KPIs; absent it, the advisor degrades to canonical-only metrics."""

    tenant_id: str
    monthly_labor_cost: Money
    monthly_other_fixed_costs: Money
    target_food_cost_bps: int = 3000  # 30% target by default
    seats: int = 0  # capacidad total del local (RevPASH); 0 = sin cargar
    daily_open_minutes: int = 0  # minutos abiertos por día (RevPASH)
    monthly_inflation_bps: int = 0  # inflación mensual estimada; 0 = sin cargar
    default_vat_bps: int = 0  # IVA global (bps); 0 = sin cargar (off), 2100 = 21%
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.target_food_cost_bps <= 10000:
            raise InvalidAdvisorSettings()
        if self.seats < 0 or self.daily_open_minutes < 0:
            raise InvalidAdvisorSettings()
        if self.monthly_inflation_bps < 0:
            raise InvalidAdvisorSettings()
        if not 0 <= self.default_vat_bps <= 10000:
            raise InvalidAdvisorSettings()
        if self.monthly_labor_cost.currency != self.monthly_other_fixed_costs.currency:
            raise CurrencyMismatch()

    @property
    def currency(self) -> str:
        return self.monthly_labor_cost.currency

    @property
    def monthly_fixed_costs(self) -> Money:
        return self.monthly_labor_cost.plus(self.monthly_other_fixed_costs)
