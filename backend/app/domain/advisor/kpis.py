"""Pure advisor KPI math (no I/O): financial ratios and break-even over the
canonical numbers. Integer minor units throughout (never float)."""

from __future__ import annotations

from dataclasses import dataclass

_DAYS_IN_MONTH = 30


def ratio_bps(part: int, whole: int) -> int:
    """``part / whole`` in basis points (e.g. 3300 = 33%); 0 when whole ≤ 0."""
    if whole <= 0:
        return 0
    return round(part * 10000 / whole)


def prorate_monthly(monthly_amount: int, period_days: int) -> int:
    """A monthly cost prorated to a period of ``period_days`` (30-day month)."""
    if period_days <= 0:
        return 0
    return round(monthly_amount * period_days / _DAYS_IN_MONTH)


def food_cost_ratio_bps(sales: int, food_cost: int) -> int:
    return ratio_bps(food_cost, sales)


def labor_cost_ratio_bps(sales: int, labor: int) -> int:
    return ratio_bps(labor, sales)


def prime_cost_ratio_bps(sales: int, food_cost: int, labor: int) -> int:
    """Prime cost = food cost + labor; the classic restaurant health metric."""
    return ratio_bps(food_cost + labor, sales)


def contribution_margin_ratio_bps(sales: int, variable_costs: int) -> int:
    """(sales − variable costs) / sales, in bps. Variable cost ≈ food cost (COGS)."""
    if sales <= 0:
        return 0
    return round((sales - variable_costs) * 10000 / sales)


def break_even_sales(fixed_costs: int, contribution_margin_bps: int) -> int:
    """Sales needed to cover fixed costs: ``fixed / contribution_margin_ratio``.
    0 when the contribution margin is non-positive (can't break even)."""
    if contribution_margin_bps <= 0:
        return 0
    return round(fixed_costs * 10000 / contribution_margin_bps)


def net_margin(sales: int, food_cost: int, labor: int, other_fixed: int) -> int:
    """Net result in minor units (may be negative — we surface the loss)."""
    return sales - food_cost - labor - other_fixed


@dataclass(frozen=True)
class AdvisorKpis:
    """The advisor's financial picture for a period. ``configured`` is False when
    the tenant hasn't loaded its fixed costs (labor/other prorate to 0 then)."""

    currency: str
    period_days: int
    sales_amount: int
    food_cost_amount: int
    labor_cost_amount: int
    other_fixed_amount: int
    waste_amount: int
    orders_count: int
    average_ticket_amount: int
    no_show_rate_bps: int
    configured: bool

    @property
    def gross_margin_amount(self) -> int:
        return self.sales_amount - self.food_cost_amount

    @property
    def net_margin_amount(self) -> int:
        return net_margin(
            self.sales_amount,
            self.food_cost_amount,
            self.labor_cost_amount,
            self.other_fixed_amount,
        )

    @property
    def food_cost_ratio_bps(self) -> int:
        return food_cost_ratio_bps(self.sales_amount, self.food_cost_amount)

    @property
    def labor_cost_ratio_bps(self) -> int:
        return labor_cost_ratio_bps(self.sales_amount, self.labor_cost_amount)

    @property
    def prime_cost_ratio_bps(self) -> int:
        return prime_cost_ratio_bps(
            self.sales_amount, self.food_cost_amount, self.labor_cost_amount
        )

    @property
    def break_even_amount(self) -> int:
        contribution = contribution_margin_ratio_bps(self.sales_amount, self.food_cost_amount)
        return break_even_sales(
            self.labor_cost_amount + self.other_fixed_amount, contribution
        )
