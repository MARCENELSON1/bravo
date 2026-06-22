"""Pure insight detection (no I/O): rules over the advisor KPIs produce the
structured insights. The numbers always come from the KPIs (the LLM layer only
re-words these later); this is the deterministic source of truth."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.advisor.kpis import AdvisorKpis
from app.domain.advisor.value_objects import InsightBucket, InsightSeverity

# Thresholds (basis points) — tunable, documented here.
_PRIME_COST_LIMIT_BPS = 6500  # 65% prime cost is the classic danger line
_NO_SHOW_LIMIT_BPS = 1000  # 10% no-show rate
_WASTE_LIMIT_BPS = 500  # merma > 5% of food cost
_FOOD_COST_CRITICAL_MARGIN_BPS = 1000  # target + 10pts → critical


@dataclass(frozen=True)
class Insight:
    """A structured advisor insight. ``data`` carries the canonical numbers the
    narrator will phrase; never recomputed downstream."""

    code: str
    severity: InsightSeverity
    bucket: InsightBucket
    data: dict[str, int]


def detect_insights(
    kpis: AdvisorKpis,
    *,
    target_food_cost_bps: int,
    previous: AdvisorKpis | None = None,
) -> list[Insight]:
    """Run every rule; return the insights that fire (order = severity later)."""
    insights: list[Insight] = []
    has_sales = kpis.sales_amount > 0

    # --- TODAY: acute / money-losing ---
    if kpis.configured and has_sales and kpis.net_margin_amount < 0:
        insights.append(
            Insight(
                code="losing_money",
                severity=InsightSeverity.CRITICAL,
                bucket=InsightBucket.TODAY,
                data={
                    "net_margin": kpis.net_margin_amount,
                    "sales": kpis.sales_amount,
                },
            )
        )
    elif kpis.configured and has_sales and kpis.sales_amount < kpis.break_even_amount:
        insights.append(
            Insight(
                code="below_break_even",
                severity=InsightSeverity.WARN,
                bucket=InsightBucket.TODAY,
                data={
                    "sales": kpis.sales_amount,
                    "break_even": kpis.break_even_amount,
                },
            )
        )

    if has_sales and kpis.food_cost_ratio_bps > target_food_cost_bps:
        over = kpis.food_cost_ratio_bps - target_food_cost_bps
        severity = (
            InsightSeverity.CRITICAL
            if over >= _FOOD_COST_CRITICAL_MARGIN_BPS
            else InsightSeverity.WARN
        )
        insights.append(
            Insight(
                code="high_food_cost",
                severity=severity,
                bucket=InsightBucket.TODAY,
                data={
                    "food_cost_ratio_bps": kpis.food_cost_ratio_bps,
                    "target_bps": target_food_cost_bps,
                },
            )
        )

    # --- THIS WEEK: worth attention ---
    if kpis.configured and has_sales and kpis.prime_cost_ratio_bps > _PRIME_COST_LIMIT_BPS:
        insights.append(
            Insight(
                code="high_prime_cost",
                severity=InsightSeverity.WARN,
                bucket=InsightBucket.THIS_WEEK,
                data={"prime_cost_ratio_bps": kpis.prime_cost_ratio_bps},
            )
        )

    if kpis.no_show_rate_bps > _NO_SHOW_LIMIT_BPS:
        insights.append(
            Insight(
                code="high_no_show",
                severity=InsightSeverity.WARN,
                bucket=InsightBucket.THIS_WEEK,
                data={"no_show_rate_bps": kpis.no_show_rate_bps},
            )
        )

    waste_ratio = _waste_ratio(kpis)
    if waste_ratio > _WASTE_LIMIT_BPS:
        insights.append(
            Insight(
                code="high_waste",
                severity=InsightSeverity.WARN,
                bucket=InsightBucket.THIS_WEEK,
                data={"waste_amount": kpis.waste_amount, "waste_ratio_bps": waste_ratio},
            )
        )

    # --- UPCOMING: setup / nudges ---
    if not kpis.configured:
        insights.append(
            Insight(
                code="configure_costs",
                severity=InsightSeverity.INFO,
                bucket=InsightBucket.UPCOMING,
                data={},
            )
        )

    # --- WELL DONE: positives ---
    if has_sales and 0 < kpis.food_cost_ratio_bps <= target_food_cost_bps:
        insights.append(
            Insight(
                code="healthy_food_cost",
                severity=InsightSeverity.GOOD,
                bucket=InsightBucket.WELL_DONE,
                data={
                    "food_cost_ratio_bps": kpis.food_cost_ratio_bps,
                    "target_bps": target_food_cost_bps,
                },
            )
        )

    if (
        previous is not None
        and previous.sales_amount > 0
        and kpis.net_margin_amount > previous.net_margin_amount
    ):
        insights.append(
            Insight(
                code="margin_improved",
                severity=InsightSeverity.GOOD,
                bucket=InsightBucket.WELL_DONE,
                data={
                    "net_margin": kpis.net_margin_amount,
                    "previous_net_margin": previous.net_margin_amount,
                },
            )
        )

    return insights


def _waste_ratio(kpis: AdvisorKpis) -> int:
    if kpis.food_cost_amount <= 0:
        return 0
    return round(kpis.waste_amount * 10000 / kpis.food_cost_amount)
