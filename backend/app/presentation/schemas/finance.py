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
    commissions_amount: int = 0
    collected_net_amount: int = 0


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


class FinanceSnapshotRebuildResponse(BaseModel):
    days: int


class ExpenseCategoryRowResponse(BaseModel):
    category: str
    amount: int
    previous: int
    delta: int


class ExpenseBreakdownResponse(BaseModel):
    currency: str
    total: int
    rows: list[ExpenseCategoryRowResponse]


class TaxCollectedResponse(BaseModel):
    currency: str
    amount: int  # sales tax cobrado en la ventana (minor units), a remitir


class TaxReportRunResponse(BaseModel):
    pending: int  # ventas que estaban por reportar en esta corrida
    sent: int  # reportadas OK al proveedor (TaxJar)
    failed: int  # fallaron y quedan para reintentar en la próxima corrida


class MovementResponse(BaseModel):
    occurred_at: str
    kind: str  # IN | OUT
    amount: int
    method: str
    category: str | None
    description: str | None
    currency: str
