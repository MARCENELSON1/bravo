"""The advisor report: compose canonical metrics + cost settings into KPIs, run
the deterministic insight rules, narrate them, and (optionally) synthesize a
summary. The numbers are always deterministic; the narrator/synthesizer only
choose words (and are no-ops by default)."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.application.clock import utcnow
from app.domain.advisor.entities import AdvisorSettings
from app.domain.advisor.insights import Insight, detect_insights
from app.domain.advisor.kpis import AdvisorKpis, prorate_monthly
from app.domain.advisor.ports import AdvisorSynthesizer, InsightNarrator, NarratedInsight
from app.domain.advisor.repository import (
    AdvisorDiagnosticsCache,
    AdvisorSettingsRepository,
    CachedDiagnostics,
)
from app.domain.identity.ports import TenantContext


def _fingerprint(insights: list[Insight], llm_enabled: bool) -> str:
    """Hash determinístico de los insights (la narración es función pura de esto
    + el proveedor). Mismo estado de datos → mismo fingerprint → cache hit."""
    parts = [
        f"{i.code}:{i.severity.value}:{i.bucket.value}:"
        + ",".join(f"{k}={i.data[k]}" for k in sorted(i.data))
        for i in insights
    ]
    raw = ("|".join(parts) + f"#llm={llm_enabled}").encode()
    return hashlib.sha256(raw).hexdigest()

_DEFAULT_TARGET_FOOD_COST_BPS = 3000


@dataclass(frozen=True)
class AdvisorMetrics:
    """Raw canonical inputs for a period (before applying the cost settings)."""

    currency: str
    sales_amount: int
    food_cost_amount: int
    orders_count: int
    waste_amount: int
    no_show_rate_bps: int


class AdvisorReadModel(ABC):
    @abstractmethod
    async def metrics(
        self, tenant_id: str, since: datetime, until: datetime
    ) -> AdvisorMetrics: ...


@dataclass(frozen=True)
class AdvisorReport:
    kpis: AdvisorKpis
    insights: list[NarratedInsight]
    summary: str | None
    llm_enabled: bool
    # KPIs del período inmediatamente anterior (misma duración) para comparativos.
    previous: AdvisorKpis | None = None


def _start_of_month(at: datetime) -> datetime:
    return at.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


class GetAdvisorReport:
    def __init__(
        self,
        read_model: AdvisorReadModel,
        settings: AdvisorSettingsRepository,
        narrator: InsightNarrator,
        synthesizer: AdvisorSynthesizer,
        tenant_context: TenantContext,
        llm_enabled: bool = False,
        cache: AdvisorDiagnosticsCache | None = None,
    ) -> None:
        self._read_model = read_model
        self._settings = settings
        self._narrator = narrator
        self._synthesizer = synthesizer
        self._tenant_context = tenant_context
        self._llm_enabled = llm_enabled
        self._cache = cache

    async def execute(
        self,
        *,
        tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> AdvisorReport:
        self._tenant_context.set(tenant_id)
        until = until or utcnow()
        since = since or _start_of_month(until)
        period_days = max(1, (until - since).days)

        settings = await self._settings.get(tenant_id)
        target = settings.target_food_cost_bps if settings else _DEFAULT_TARGET_FOOD_COST_BPS

        metrics = await self._read_model.metrics(tenant_id, since, until)
        kpis = self._build_kpis(metrics, settings, period_days)

        prev_metrics = await self._read_model.metrics(
            tenant_id, since - timedelta(days=period_days), since
        )
        previous = self._build_kpis(prev_metrics, settings, period_days)

        insights = detect_insights(kpis, target_food_cost_bps=target, previous=previous)
        # Fase 9.1 — caché de diagnostics (capa 3 del doc): con narrador/synthesizer
        # LLM, narrar cuesta ~N+1 llamadas por request. Cuando hay caché y el LLM está
        # prendido, se sirve por fingerprint (insights+proveedor) y solo se regenera
        # cuando cambia la data. Con narrador=template (default) es instantáneo → no
        # se cachea (evita escrituras inútiles ante data que cambia con cada venta).
        narrated, summary = await self._narrate(tenant_id, kpis, insights)
        return AdvisorReport(
            kpis=kpis,
            insights=narrated,
            summary=summary,
            llm_enabled=self._llm_enabled,
            previous=previous,
        )

    async def _narrate(
        self, tenant_id: str, kpis: AdvisorKpis, insights: list[Insight]
    ) -> tuple[list[NarratedInsight], str | None]:
        if self._llm_enabled and self._cache is not None:
            fingerprint = _fingerprint(insights, self._llm_enabled)
            cached = await self._cache.get(tenant_id, fingerprint)
            if cached is not None:
                return cached.insights, cached.summary
            narrated = [await self._narrator.narrate(i) for i in insights]
            summary = await self._synthesizer.synthesize(kpis, narrated)
            await self._cache.put(
                tenant_id,
                fingerprint,
                CachedDiagnostics(insights=narrated, summary=summary, generated_at=utcnow()),
            )
            return narrated, summary
        narrated = [await self._narrator.narrate(i) for i in insights]
        summary = await self._synthesizer.synthesize(kpis, narrated)
        return narrated, summary

    @staticmethod
    def _build_kpis(
        metrics: AdvisorMetrics, settings: AdvisorSettings | None, period_days: int
    ) -> AdvisorKpis:
        labor = (
            prorate_monthly(settings.monthly_labor_cost.amount, period_days)
            if settings
            else 0
        )
        other = (
            prorate_monthly(settings.monthly_other_fixed_costs.amount, period_days)
            if settings
            else 0
        )
        avg_ticket = (
            metrics.sales_amount // metrics.orders_count if metrics.orders_count else 0
        )
        return AdvisorKpis(
            currency=metrics.currency,
            period_days=period_days,
            sales_amount=metrics.sales_amount,
            food_cost_amount=metrics.food_cost_amount,
            labor_cost_amount=labor,
            other_fixed_amount=other,
            waste_amount=metrics.waste_amount,
            orders_count=metrics.orders_count,
            average_ticket_amount=avg_ticket,
            no_show_rate_bps=metrics.no_show_rate_bps,
            configured=settings is not None,
        )
