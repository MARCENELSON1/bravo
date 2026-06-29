from __future__ import annotations

from app.application.finance.use_cases import _build_finance_kpis
from app.domain.advisor.kpis import AdvisorKpis


def _kpis(*, sales: int, food: int, labor: int, waste: int = 0) -> AdvisorKpis:
    return AdvisorKpis(
        currency="ARS",
        period_days=30,
        sales_amount=sales,
        food_cost_amount=food,
        labor_cost_amount=labor,
        other_fixed_amount=0,
        waste_amount=waste,
        orders_count=10,
        average_ticket_amount=sales // 10 if sales else 0,
        no_show_rate_bps=0,
        configured=True,
    )


def _by_key(kpis: list) -> dict:
    return {k.key: k for k in kpis}


def test_healthy_food_and_labor_are_flagged_healthy() -> None:
    # food 30% (3000 bps), labor 30% → ambos dentro del rango sano.
    cur = _kpis(sales=1_000_000, food=300_000, labor=300_000)
    kpis = _by_key(_build_finance_kpis(cur, None))
    assert kpis["food_cost"].value == 3000
    assert kpis["food_cost"].status == "healthy"
    assert kpis["labor_cost"].status == "healthy"


def test_prime_cost_alert_above_65pct() -> None:
    # food 40% + labor 30% = prime 70% → alert (>6500).
    cur = _kpis(sales=1_000_000, food=400_000, labor=300_000)
    prime = _by_key(_build_finance_kpis(cur, None))["prime_cost"]
    assert prime.value == 7000
    assert prime.status == "alert"


def test_waste_ratio_over_sales_and_alert() -> None:
    # mermas 5% de la facturación → arriba del 3% sano.
    cur = _kpis(sales=1_000_000, food=300_000, labor=200_000, waste=50_000)
    waste = _by_key(_build_finance_kpis(cur, None))["waste"]
    assert waste.value == 500  # 5%
    assert waste.status == "alert"


def test_delta_vs_previous_period() -> None:
    cur = _kpis(sales=1_000_000, food=350_000, labor=300_000)
    prev = _kpis(sales=1_000_000, food=300_000, labor=300_000)
    food = _by_key(_build_finance_kpis(cur, prev))["food_cost"]
    assert food.value == 3500 and food.previous == 3000
    assert food.delta == 500  # subió 5 puntos


def test_no_previous_period_zeroes_the_baseline() -> None:
    cur = _kpis(sales=1_000_000, food=300_000, labor=300_000)
    food = _by_key(_build_finance_kpis(cur, None))["food_cost"]
    assert food.previous == 0 and food.delta == food.value


def test_net_margin_negative_is_alert() -> None:
    # costos > ventas → margen neto negativo.
    cur = _kpis(sales=100_000, food=80_000, labor=80_000)
    net = _by_key(_build_finance_kpis(cur, None))["net_margin"]
    assert net.value < 0 and net.status == "alert"
