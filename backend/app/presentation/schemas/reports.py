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
    collected_net: int = 0  # neto financiero (tras comisiones); == sales sin tasas
    fees_total: int = 0


class StaffReportRowResponse(BaseModel):
    user_id: str
    email: str
    worked_minutes: int
    overtime_minutes: int
    tables_served: int
    sales_amount: int  # minor units
    hourly_rate_amount: int | None  # valor/hora en minor units; null → sin cargar
    currency: str


class StaffReportResponse(BaseModel):
    currency: str
    rows: list[StaffReportRowResponse]
