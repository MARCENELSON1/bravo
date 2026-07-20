"""Tanda D Finanzas: labor real (horas × rate) con fallback al mensual prorrateado."""

from __future__ import annotations

from datetime import datetime

from app.application.advisor.report import (
    AdvisorMetrics,
    AdvisorReadModel,
    GetAdvisorReport,
    LaborCostReadModel,
)
from app.domain.advisor.entities import AdvisorSettings
from app.domain.advisor.insights import Insight
from app.domain.advisor.kpis import AdvisorKpis, prorate_monthly
from app.domain.advisor.ports import AdvisorSynthesizer, InsightNarrator, NarratedInsight
from app.domain.advisor.repository import AdvisorSettingsRepository
from app.domain.shared.money import Money
from tests.fakes import FakeTenantContext


class _ReadModel(AdvisorReadModel):
    async def metrics(self, tenant_id: str, since: datetime, until: datetime) -> AdvisorMetrics:
        return AdvisorMetrics(
            currency="ARS",
            sales_amount=1_000_000,
            food_cost_amount=300_000,
            orders_count=10,
            waste_amount=0,
            no_show_rate_bps=0,
        )


class _Settings(AdvisorSettingsRepository):
    def __init__(self, monthly_labor: int) -> None:
        self._monthly = monthly_labor

    async def get(self, tenant_id: str) -> AdvisorSettings | None:
        return AdvisorSettings(
            tenant_id=tenant_id,
            monthly_labor_cost=Money(self._monthly, "ARS"),
            monthly_other_fixed_costs=Money(0, "ARS"),
            target_food_cost_bps=3000,
        )

    async def save(self, settings: AdvisorSettings) -> None: ...


class _Labor(LaborCostReadModel):
    def __init__(self, total: int) -> None:
        self._total = total

    async def total(self, tenant_id: str, since: datetime, until: datetime) -> int:
        return self._total


class _Narrator(InsightNarrator):
    async def narrate(self, insight: Insight) -> NarratedInsight:
        return NarratedInsight(
            code=insight.code, severity=insight.severity.value,
            bucket=insight.bucket.value, title="t", body="b", action="a",
        )


class _NoSynthesis(AdvisorSynthesizer):
    async def synthesize(self, kpis: AdvisorKpis, narrated: list[NarratedInsight]) -> str | None:
        return None


async def _report(labor: LaborCostReadModel | None, monthly_labor: int = 900_000):
    use_case = GetAdvisorReport(
        read_model=_ReadModel(),
        settings=_Settings(monthly_labor),
        narrator=_Narrator(),
        synthesizer=_NoSynthesis(),
        tenant_context=FakeTenantContext(),
        labor=labor,
    )
    return await use_case.execute(tenant_id="t1")


async def test_labor_uses_real_hours_when_rates_exist() -> None:
    # 480 min × $2000/h en minor units → el KPI deja de ser el prorrateo.
    report = await _report(labor=_Labor(total=1_600_000))
    assert report.kpis.labor_cost_amount == 1_600_000
    assert report.previous is not None
    assert report.previous.labor_cost_amount == 1_600_000  # comparativo consistente


async def test_labor_falls_back_to_prorated_monthly_without_rates() -> None:
    # Sin rates/turnos el read model devuelve 0 → mensual prorrateado (como antes).
    report = await _report(labor=_Labor(total=0))
    expected = prorate_monthly(900_000, report.kpis.period_days)
    assert report.kpis.labor_cost_amount == expected


async def test_labor_without_read_model_keeps_previous_behaviour() -> None:
    report = await _report(labor=None)
    expected = prorate_monthly(900_000, report.kpis.period_days)
    assert report.kpis.labor_cost_amount == expected
