from __future__ import annotations

from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    """Resumen del período. Cada importe dice sobre qué base está medido.

    Hubo por un rato un alias ``sales``/``net`` para no romper una build vieja;
    se sacó a pedido, subiendo una build nueva en su lugar. Queda anotado porque
    es la decisión que importa: **un nombre que engaña no se deja "por
    compatibilidad"** — se renombra y se actualiza el cliente.
    """

    currency: str
    # Lo COBRADO en el período (Σ cobros confirmados), bruto de comisiones. Lo
    # VENDIDO —otro libro— se pide a `/analytics/revenue` como `sales_amount`.
    sales_collected: int  # minor units
    expenses: int
    # Las dos ganancias, nombradas por su base: antes y después de la comisión.
    profit_gross_of_fees: int  # sales_collected − expenses
    active_orders: int
    paid_orders: int
    avg_ticket: int
    payment_count: int
    collected_net: int = 0  # cobrado neto de comisiones
    fees_total: int = 0
    profit_net_of_fees: int = 0  # collected_net − expenses


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
