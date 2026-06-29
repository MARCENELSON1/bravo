from __future__ import annotations

from pydantic import BaseModel


class FinanceKpiResponse(BaseModel):
    key: str
    kind: str  # "ratio" (bps) | "money" (minor units)
    value: int
    previous: int
    delta: int
    healthy_low: int | None
    healthy_high: int | None
    status: str  # healthy | warn | alert | neutral


class FinanceDiagnosticResponse(BaseModel):
    code: str
    severity: str
    bucket: str
    title: str
    body: str
    action: str


class ProductMarginResponse(BaseModel):
    product_id: str
    product_name: str
    units_sold: int
    sales_amount: int
    margin_amount: int


class FinanceOverviewResponse(BaseModel):
    currency: str
    period_days: int
    configured: bool
    kpis: list[FinanceKpiResponse]
    diagnostics: list[FinanceDiagnosticResponse]
    product_margins: list[ProductMarginResponse]
    summary: str | None
