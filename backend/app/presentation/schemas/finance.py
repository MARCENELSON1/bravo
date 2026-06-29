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


class FinanceProjectionResponse(BaseModel):
    sales_amount: int
    net_margin_amount: int
    month_days: int
    elapsed_days: int


class FinanceOverviewResponse(BaseModel):
    currency: str
    period_days: int
    configured: bool
    kpis: list[FinanceKpiResponse]
    diagnostics: list[FinanceDiagnosticResponse]
    product_margins: list[ProductMarginResponse]
    summary: str | None
    projection: FinanceProjectionResponse | None = None


class ProductSaleLineResponse(BaseModel):
    order_id: str
    occurred_at: str
    quantity: int
    line_amount: int
    food_cost_amount: int | None
    margin_amount: int


class ProductDetailResponse(BaseModel):
    product_id: str
    currency: str
    units_sold: int
    sales_amount: int
    food_cost_amount: int
    margin_amount: int
    lines: list[ProductSaleLineResponse]
