from __future__ import annotations

from datetime import date

from pydantic import BaseModel

# All amounts are integer minor units (centavos) in the tenant's currency.


class RevenueSummaryResponse(BaseModel):
    currency: str
    sales_amount: int
    collected_amount: int
    expense_amount: int
    food_cost_amount: int
    gross_margin_amount: int
    orders_count: int
    average_ticket_amount: int


class RevenueDailyPointResponse(BaseModel):
    day: date
    sales_amount: int
    orders_count: int


class PaymentMixRowResponse(BaseModel):
    method: str
    direction: str
    amount: int
    count: int


class ProductPerformanceRowResponse(BaseModel):
    product_id: str
    product_name: str
    units_sold: int
    sales_amount: int
    food_cost_amount: int
    margin_amount: int
    currency: str


class RebuildResponse(BaseModel):
    projected: int
