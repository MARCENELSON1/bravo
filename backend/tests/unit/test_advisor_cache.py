from __future__ import annotations

from datetime import datetime

from app.application.advisor.report import (
    AdvisorMetrics,
    AdvisorReadModel,
    GetAdvisorReport,
    _fingerprint,
)
from app.application.advisor.use_cases import RebuildAdvisorDiagnostics
from app.domain.advisor.entities import AdvisorSettings
from app.domain.advisor.insights import Insight
from app.domain.advisor.kpis import AdvisorKpis
from app.domain.advisor.ports import AdvisorSynthesizer, InsightNarrator, NarratedInsight
from app.domain.advisor.repository import (
    AdvisorDiagnosticsCache,
    AdvisorSettingsRepository,
    CachedDiagnostics,
)
from app.domain.advisor.value_objects import InsightBucket, InsightSeverity
from tests.fakes import FakeTenantContext


def _insight(code: str, **data: int) -> Insight:
    return Insight(
        code=code, severity=InsightSeverity.WARN, bucket=InsightBucket.TODAY, data=data
    )


def test_fingerprint_is_stable_and_data_sensitive() -> None:
    a = [_insight("high_food_cost", food_cost_ratio_bps=4000)]
    b = [_insight("high_food_cost", food_cost_ratio_bps=4000)]
    c = [_insight("high_food_cost", food_cost_ratio_bps=3800)]
    assert _fingerprint(a, True) == _fingerprint(b, True)  # mismos datos → mismo hash
    assert _fingerprint(a, True) != _fingerprint(c, True)  # cambia un número → cambia
    assert _fingerprint(a, True) != _fingerprint(a, False)  # cambia proveedor → cambia


class _ReadModel(AdvisorReadModel):
    def __init__(self, metrics: AdvisorMetrics) -> None:
        self.metrics_value = metrics

    async def metrics(self, tenant_id: str, since: datetime, until: datetime) -> AdvisorMetrics:
        return self.metrics_value


class _NoSettings(AdvisorSettingsRepository):
    async def get(self, tenant_id: str) -> AdvisorSettings | None:
        return None

    async def save(self, settings: AdvisorSettings) -> None: ...


class _CountingNarrator(InsightNarrator):
    def __init__(self) -> None:
        self.calls = 0

    async def narrate(self, insight: Insight) -> NarratedInsight:
        self.calls += 1
        return NarratedInsight(
            code=insight.code,
            severity=insight.severity.value,
            bucket=insight.bucket.value,
            title="t",
            body="b",
            action="a",
        )


class _NoSynthesis(AdvisorSynthesizer):
    async def synthesize(self, kpis: AdvisorKpis, narrated: list[NarratedInsight]) -> str | None:
        return None


class _MemCache(AdvisorDiagnosticsCache):
    def __init__(self) -> None:
        self.store: dict[tuple[str, str], CachedDiagnostics] = {}

    async def get(self, tenant_id: str, fingerprint: str) -> CachedDiagnostics | None:
        return self.store.get((tenant_id, fingerprint))

    async def put(
        self, tenant_id: str, fingerprint: str, diagnostics: CachedDiagnostics
    ) -> None:
        self.store[(tenant_id, fingerprint)] = diagnostics

    async def purge(self, tenant_id: str) -> int:
        keys = [k for k in self.store if k[0] == tenant_id]
        for k in keys:
            del self.store[k]
        return len(keys)


def _metrics(food: int) -> AdvisorMetrics:
    return AdvisorMetrics(
        currency="ARS",
        sales_amount=100_000,
        food_cost_amount=food,
        orders_count=10,
        waste_amount=0,
        no_show_rate_bps=0,
    )


async def _report(read_model, narrator, cache, *, llm_enabled):
    use_case = GetAdvisorReport(
        read_model=read_model,
        settings=_NoSettings(),
        narrator=narrator,
        synthesizer=_NoSynthesis(),
        tenant_context=FakeTenantContext(),
        llm_enabled=llm_enabled,
        cache=cache,
    )
    return await use_case.execute(tenant_id="t1")


async def test_cache_serves_without_re_narrating() -> None:
    read_model = _ReadModel(_metrics(food=50_000))  # food cost 50% → dispara insight
    narrator = _CountingNarrator()
    cache = _MemCache()

    first = await _report(read_model, narrator, cache, llm_enabled=True)
    assert first.insights  # hubo al menos un diagnóstico
    calls_after_first = narrator.calls
    assert calls_after_first > 0

    # Segunda apertura, misma data → cache hit, no se vuelve a narrar (no llama al LLM).
    await _report(read_model, narrator, cache, llm_enabled=True)
    assert narrator.calls == calls_after_first

    # Cambia la data (otro food cost) → otro fingerprint → se regenera.
    read_model.metrics_value = _metrics(food=20_000)
    await _report(read_model, narrator, cache, llm_enabled=True)
    assert narrator.calls > calls_after_first


async def test_cache_is_skipped_when_llm_is_off() -> None:
    # Con narrador template (llm off) no se cachea: narra siempre (es instantáneo).
    read_model = _ReadModel(_metrics(food=50_000))
    narrator = _CountingNarrator()
    cache = _MemCache()

    await _report(read_model, narrator, cache, llm_enabled=False)
    await _report(read_model, narrator, cache, llm_enabled=False)
    assert not cache.store  # nada cacheado
    assert narrator.calls > 0


async def test_rebuild_purges_only_the_tenant_and_regenerates() -> None:
    read_model = _ReadModel(_metrics(food=50_000))
    narrator = _CountingNarrator()
    cache = _MemCache()

    await _report(read_model, narrator, cache, llm_enabled=True)
    calls_after_first = narrator.calls
    assert cache.store  # quedó cacheado

    # Entrada de OTRO tenant: el purge no debe tocarla.
    other = CachedDiagnostics(insights=[], summary=None, generated_at=datetime(2026, 1, 1))
    await cache.put("t2", "fp-otro", other)

    rebuild = RebuildAdvisorDiagnostics(cache=cache, tenant_context=FakeTenantContext())
    purged = await rebuild.execute(tenant_id="t1")
    assert purged == 1
    assert ("t2", "fp-otro") in cache.store  # aislamiento por tenant

    # Sin caché, el próximo request vuelve a narrar.
    await _report(read_model, narrator, cache, llm_enabled=True)
    assert narrator.calls > calls_after_first
