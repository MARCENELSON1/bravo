"""Tanda E Finanzas: RevPASH (ventas/asiento-hora) y rotación de inventario."""

from __future__ import annotations

from app.application.finance.use_cases import _revpash_kpi, _turnover_kpi
from app.domain.advisor.entities import AdvisorSettings
from app.domain.advisor.kpis import AdvisorKpis
from app.domain.shared.money import Money


def _kpis(*, sales: int, food: int = 0, days: int = 1) -> AdvisorKpis:
    return AdvisorKpis(
        currency="ARS", period_days=days, sales_amount=sales, food_cost_amount=food,
        labor_cost_amount=0, other_fixed_amount=0, waste_amount=0, orders_count=1,
        average_ticket_amount=sales, no_show_rate_bps=0, configured=True,
    )


def _settings(*, seats: int, open_min: int) -> AdvisorSettings:
    return AdvisorSettings(
        tenant_id="t1", monthly_labor_cost=Money(0, "ARS"),
        monthly_other_fixed_costs=Money(0, "ARS"), seats=seats, daily_open_minutes=open_min,
    )


def test_revpash_divides_sales_by_seat_hours() -> None:
    # 20 asientos × 8h × 1 día = 160 asiento-hora; ventas 320000 → 2000/asiento-hora.
    kpi = _revpash_kpi(_kpis(sales=320_000), None, _settings(seats=20, open_min=480))
    assert kpi.key == "revpash"
    assert kpi.kind == "money"
    assert kpi.value == 2000


def test_revpash_is_zero_without_seats_or_hours() -> None:
    assert _revpash_kpi(_kpis(sales=100_000), None, _settings(seats=0, open_min=480)).value == 0
    assert _revpash_kpi(_kpis(sales=100_000), None, _settings(seats=10, open_min=0)).value == 0
    assert _revpash_kpi(_kpis(sales=100_000), None, None).value == 0  # sin settings


def test_revpash_carries_previous_for_comparison() -> None:
    kpi = _revpash_kpi(
        _kpis(sales=320_000), _kpis(sales=160_000), _settings(seats=20, open_min=480)
    )
    assert kpi.value == 2000
    assert kpi.previous == 1000
    assert kpi.delta == 1000


def test_turnover_is_cogs_over_inventory_in_centis() -> None:
    # COGS 500000 / inventario 200000 = 2,5× → 250 centésimas.
    kpi = _turnover_kpi(_kpis(sales=1_000_000, food=500_000), inventory_value=200_000)
    assert kpi.key == "inventory_turnover"
    assert kpi.kind == "turnover"
    assert kpi.value == 250
    assert kpi.delta == 0  # sin histórico de inventario


def test_turnover_is_zero_without_inventory() -> None:
    assert _turnover_kpi(_kpis(sales=1_000_000, food=500_000), inventory_value=0).value == 0
