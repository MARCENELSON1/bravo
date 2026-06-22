from __future__ import annotations

from pydantic import BaseModel, Field

# Amounts are integer minor units (centavos); ratios in basis points.


class AdvisorKpisResponse(BaseModel):
    currency: str
    period_days: int
    sales_amount: int
    food_cost_amount: int
    labor_cost_amount: int
    other_fixed_amount: int
    waste_amount: int
    gross_margin_amount: int
    net_margin_amount: int
    food_cost_ratio_bps: int
    labor_cost_ratio_bps: int
    prime_cost_ratio_bps: int
    break_even_amount: int
    orders_count: int
    average_ticket_amount: int
    no_show_rate_bps: int
    configured: bool


class NarratedInsightResponse(BaseModel):
    code: str
    severity: str
    bucket: str
    title: str
    body: str
    action: str


class AdvisorReportResponse(BaseModel):
    kpis: AdvisorKpisResponse
    insights: list[NarratedInsightResponse]
    summary: str | None
    llm_enabled: bool


class AdvisorSettingsResponse(BaseModel):
    monthly_labor_cost: int
    monthly_other_fixed_costs: int
    target_food_cost_bps: int
    currency: str
    configured: bool


class UpdateAdvisorSettingsRequest(BaseModel):
    monthly_labor_cost: int = Field(ge=0)
    monthly_other_fixed_costs: int = Field(ge=0)
    target_food_cost_bps: int = Field(ge=0, le=10000)
