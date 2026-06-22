from __future__ import annotations

import pytest

from app.domain.advisor.entities import AdvisorSettings
from app.domain.advisor.exceptions import InvalidAdvisorSettings
from app.domain.advisor.insights import detect_insights
from app.domain.advisor.kpis import (
    AdvisorKpis,
    break_even_sales,
    contribution_margin_ratio_bps,
    food_cost_ratio_bps,
    net_margin,
    prime_cost_ratio_bps,
    prorate_monthly,
)
from app.domain.advisor.value_objects import InsightBucket, InsightSeverity
from app.domain.shared.exceptions import CurrencyMismatch
from app.domain.shared.money import Money

# --- KPIs (pure) ----------------------------------------------------------


def test_food_cost_ratio_bps() -> None:
    assert food_cost_ratio_bps(1000, 330) == 3300
    assert food_cost_ratio_bps(0, 330) == 0  # no sales → 0


def test_prime_cost_ratio_bps() -> None:
    assert prime_cost_ratio_bps(1000, 300, 350) == 6500  # (300+350)/1000


def test_contribution_margin_and_break_even() -> None:
    cm = contribution_margin_ratio_bps(1000, 300)  # (1000-300)/1000 = 70%
    assert cm == 7000
    # fixed 700 / 0.70 = 1000
    assert break_even_sales(700, cm) == 1000
    assert break_even_sales(700, 0) == 0  # no contribution → can't break even


def test_net_margin_can_be_negative() -> None:
    assert net_margin(1000, 300, 350, 200) == 150
    assert net_margin(1000, 500, 400, 300) == -200


def test_prorate_monthly() -> None:
    assert prorate_monthly(300000, 30) == 300000
    assert prorate_monthly(300000, 15) == 150000
    assert prorate_monthly(300000, 0) == 0


# --- AdvisorSettings ------------------------------------------------------


def test_settings_currency_and_fixed_costs() -> None:
    s = AdvisorSettings(
        tenant_id="t1",
        monthly_labor_cost=Money(300000, "ARS"),
        monthly_other_fixed_costs=Money(200000, "ARS"),
    )
    assert s.currency == "ARS"
    assert s.monthly_fixed_costs == Money(500000, "ARS")
    assert s.target_food_cost_bps == 3000


def test_settings_rejects_bad_target() -> None:
    with pytest.raises(InvalidAdvisorSettings):
        AdvisorSettings(
            tenant_id="t1",
            monthly_labor_cost=Money(0, "ARS"),
            monthly_other_fixed_costs=Money(0, "ARS"),
            target_food_cost_bps=20000,
        )


def test_settings_rejects_currency_mismatch() -> None:
    with pytest.raises(CurrencyMismatch):
        AdvisorSettings(
            tenant_id="t1",
            monthly_labor_cost=Money(1, "ARS"),
            monthly_other_fixed_costs=Money(1, "USD"),
        )


# --- detect_insights ------------------------------------------------------


def _kpis(**overrides) -> AdvisorKpis:
    base = dict(
        currency="ARS",
        period_days=30,
        sales_amount=1_000_000,
        food_cost_amount=300_000,
        labor_cost_amount=300_000,
        other_fixed_amount=200_000,
        waste_amount=0,
        orders_count=100,
        average_ticket_amount=10_000,
        no_show_rate_bps=0,
        configured=True,
    )
    base.update(overrides)
    return AdvisorKpis(**base)  # type: ignore[arg-type]


def _codes(insights) -> set[str]:
    return {i.code for i in insights}


def test_healthy_food_cost_is_good() -> None:
    insights = detect_insights(_kpis(), target_food_cost_bps=3500)
    healthy = next(i for i in insights if i.code == "healthy_food_cost")
    assert healthy.severity is InsightSeverity.GOOD
    assert healthy.bucket is InsightBucket.WELL_DONE


def test_high_food_cost_warns_then_critical() -> None:
    # 40% vs 30% target → over by 1000 → CRITICAL
    insights = detect_insights(
        _kpis(food_cost_amount=400_000), target_food_cost_bps=3000
    )
    high = next(i for i in insights if i.code == "high_food_cost")
    assert high.severity is InsightSeverity.CRITICAL
    assert high.bucket is InsightBucket.TODAY


def test_losing_money_is_critical() -> None:
    insights = detect_insights(
        _kpis(food_cost_amount=500_000, labor_cost_amount=400_000, other_fixed_amount=300_000),
        target_food_cost_bps=3000,
    )
    assert "losing_money" in _codes(insights)


def test_high_no_show_warns() -> None:
    insights = detect_insights(_kpis(no_show_rate_bps=1500), target_food_cost_bps=3500)
    assert "high_no_show" in _codes(insights)


def test_high_waste_warns() -> None:
    # waste 30000 over food 300000 = 10% > 5%
    insights = detect_insights(_kpis(waste_amount=30_000), target_food_cost_bps=3500)
    assert "high_waste" in _codes(insights)


def test_unconfigured_prompts_to_configure() -> None:
    insights = detect_insights(
        _kpis(configured=False, labor_cost_amount=0, other_fixed_amount=0),
        target_food_cost_bps=3000,
    )
    assert "configure_costs" in _codes(insights)
    # No labor-dependent insight when unconfigured.
    assert "high_prime_cost" not in _codes(insights)


def test_margin_improved_vs_previous() -> None:
    previous = _kpis(sales_amount=1_000_000, food_cost_amount=400_000)
    insights = detect_insights(
        _kpis(food_cost_amount=300_000), target_food_cost_bps=3500, previous=previous
    )
    improved = next(i for i in insights if i.code == "margin_improved")
    assert improved.severity is InsightSeverity.GOOD
