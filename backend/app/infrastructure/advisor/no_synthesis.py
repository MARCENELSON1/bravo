"""Default synthesizer: no summary (the LLM layer is off). Deterministic."""

from __future__ import annotations

from app.domain.advisor.kpis import AdvisorKpis
from app.domain.advisor.ports import AdvisorSynthesizer, NarratedInsight


class NoSynthesis(AdvisorSynthesizer):
    async def synthesize(
        self, kpis: AdvisorKpis, narrated: list[NarratedInsight]
    ) -> str | None:
        return None
