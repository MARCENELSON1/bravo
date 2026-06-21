from __future__ import annotations

from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    currency: str
    sales: int  # minor units
    expenses: int
    net: int
    active_orders: int
    paid_orders: int
    avg_ticket: int
    payment_count: int
