from __future__ import annotations

from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    """Resumen del período. Cada importe dice sobre qué base está medido.

    **Sobre ``sales`` y ``net``:** son los nombres VIEJOS de ``sales_collected``
    y ``profit_gross_of_fees``, y se siguen enviando con el mismo valor. No es
    indecisión: los lee una app móvil ya publicada, y sacarlos de la respuesta le
    mostraría $0 a quien todavía no actualizó. Se borran cuando no quede ninguna
    build en circulación anterior a la que consume los nombres nuevos — el test
    ``test_dashboard_deprecated_aliases_match_new_names`` es el que garantiza,
    mientras tanto, que las dos versiones ven exactamente el mismo número.
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

    # --- Alias deprecados (ver docstring). No usar en código nuevo. ---
    sales: int = 0
    net: int = 0


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
