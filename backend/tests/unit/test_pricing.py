"""Productos v2 Tanda B — cálculo de "debería estar en $X" (unit, sin DB)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.application.product.dtos import ProductPricingBase
from app.application.product.use_cases import (
    GetPricingInsights,
    suggested_price_amount,
)
from app.domain.advisor.entities import AdvisorSettings
from app.domain.shared.money import Money


def test_suggested_price_no_inflation_is_unchanged() -> None:
    assert suggested_price_amount(100000, 0, 90) == 100000


def test_suggested_price_zero_days_is_unchanged() -> None:
    assert suggested_price_amount(100000, 2000, 0) == 100000


def test_suggested_price_one_month_applies_monthly_rate() -> None:
    # 20% mensual, 30 días → +20%.
    assert suggested_price_amount(100000, 2000, 30) == 120000


def test_suggested_price_compounds_over_two_months() -> None:
    # 20% mensual, 60 días → 1.2^2 = 1.44.
    assert suggested_price_amount(100000, 2000, 60) == 144000


def test_suggested_price_non_positive_base() -> None:
    assert suggested_price_amount(0, 2000, 60) == 0


class _FakePricingReadModel:
    def __init__(self, currency: str, rows: list[ProductPricingBase]) -> None:
        self._currency = currency
        self._rows = rows

    async def base_rows(self, tenant_id: str):
        return self._currency, self._rows


class _FakeSettingsRepo:
    def __init__(self, settings: AdvisorSettings | None) -> None:
        self._settings = settings

    async def get(self, tenant_id: str):
        return self._settings

    async def save(self, settings) -> None:  # pragma: no cover - unused
        self._settings = settings


class _FakeTenantContext:
    def set(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id


def _settings(bps: int) -> AdvisorSettings:
    return AdvisorSettings(
        tenant_id="t1",
        monthly_labor_cost=Money(0, "ARS"),
        monthly_other_fixed_costs=Money(0, "ARS"),
        monthly_inflation_bps=bps,
    )


async def test_pricing_insights_flags_lagging_and_sorts() -> None:
    now = datetime(2026, 8, 1, tzinfo=UTC)
    rows = [
        ProductPricingBase(
            product_id="p-old",
            product_name="Milanesa",
            current_price_amount=100000,
            last_change_at=now - timedelta(days=60),  # rezagado
        ),
        ProductPricingBase(
            product_id="p-fresh",
            product_name="Gaseosa",
            current_price_amount=50000,
            last_change_at=now,  # recién cambiado → sin gap
        ),
    ]
    use_case = GetPricingInsights(
        pricing=_FakePricingReadModel("ARS", rows),
        settings=_FakeSettingsRepo(_settings(2000)),  # 20% mensual
        tenant_context=_FakeTenantContext(),
    )

    insights = await use_case.execute(tenant_id="t1", now=now)

    assert insights.configured is True
    assert insights.monthly_inflation_bps == 2000
    # Ordenado por gap desc: el rezagado primero.
    assert insights.rows[0].product_id == "p-old"
    assert insights.rows[0].suggested_price_amount == 144000
    assert insights.rows[0].gap_amount == 44000
    assert insights.rows[0].days_since_change == 60
    assert insights.rows[0].lagging is True
    # El recién cambiado: sin gap, no rezagado.
    assert insights.rows[1].product_id == "p-fresh"
    assert insights.rows[1].suggested_price_amount == 50000
    assert insights.rows[1].lagging is False


async def test_pricing_insights_without_inflation_is_not_configured() -> None:
    now = datetime(2026, 8, 1, tzinfo=UTC)
    rows = [
        ProductPricingBase(
            product_id="p1",
            product_name="Milanesa",
            current_price_amount=100000,
            last_change_at=now - timedelta(days=90),
        ),
    ]
    use_case = GetPricingInsights(
        pricing=_FakePricingReadModel("ARS", rows),
        settings=_FakeSettingsRepo(None),  # sin settings cargados
        tenant_context=_FakeTenantContext(),
    )

    insights = await use_case.execute(tenant_id="t1", now=now)

    assert insights.configured is False
    assert insights.rows[0].suggested_price_amount == 100000
    assert insights.rows[0].lagging is False
