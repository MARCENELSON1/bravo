"""The LLM narrator/synthesizer use a FAKE client (no network). Verifies the
grounding guardrail: hallucinated numbers are rejected, falling back to the
deterministic template."""

from __future__ import annotations

import pytest

from app.domain.advisor.insights import Insight
from app.domain.advisor.value_objects import InsightBucket, InsightSeverity
from app.infrastructure.advisor.claude_narrator import ClaudeNarrator
from app.infrastructure.advisor.claude_synthesizer import ClaudeSynthesizer
from app.infrastructure.advisor.llm import AdvisorLLMClient
from app.infrastructure.advisor.template_narrator import TemplateNarrator

pytestmark = pytest.mark.asyncio


class _FakeLLM(AdvisorLLMClient):
    def __init__(self, reply: str | Exception) -> None:
        self._reply = reply

    async def complete(self, *, system: str, user: str) -> str:
        if isinstance(self._reply, Exception):
            raise self._reply
        return self._reply


def _insight() -> Insight:
    # high_food_cost → template mentions "40%" and "30%".
    return Insight(
        code="high_food_cost",
        severity=InsightSeverity.CRITICAL,
        bucket=InsightBucket.TODAY,
        data={"food_cost_ratio_bps": 4000, "target_bps": 3000},
    )


async def test_narrator_uses_llm_text_when_grounded() -> None:
    # Reply restates only the allowed numbers (40, 30).
    llm = _FakeLLM("Tu food cost trepó a 40% contra un objetivo de 30%, ojo con eso.")
    narrator = ClaudeNarrator(llm=llm, fallback=TemplateNarrator())
    result = await narrator.narrate(_insight())
    assert "40%" in result.body
    assert "ojo con eso" in result.body  # came from the LLM, not the template


async def test_narrator_rejects_hallucinated_number() -> None:
    # 999 is NOT in the grounded base → guardrail trips → template fallback.
    llm = _FakeLLM("Perdiste 999 lucas por el food cost altísimo.")
    template = TemplateNarrator()
    narrator = ClaudeNarrator(llm=llm, fallback=template)
    result = await narrator.narrate(_insight())
    expected = await template.narrate(_insight())
    assert result.body == expected.body  # fell back to the deterministic copy


async def test_narrator_falls_back_on_llm_error() -> None:
    narrator = ClaudeNarrator(llm=_FakeLLM(RuntimeError("boom")), fallback=TemplateNarrator())
    result = await narrator.narrate(_insight())
    assert result.body  # deterministic body, no crash


async def test_synthesizer_returns_none_on_hallucination() -> None:
    template = TemplateNarrator()
    narrated = [await template.narrate(_insight())]
    synth = ClaudeSynthesizer(llm=_FakeLLM("Facturaste 123456789 este mes."))
    assert await synth.synthesize(kpis=None, narrated=narrated) is None  # type: ignore[arg-type]


async def test_synthesizer_returns_text_when_grounded() -> None:
    template = TemplateNarrator()
    narrated = [await template.narrate(_insight())]
    synth = ClaudeSynthesizer(llm=_FakeLLM("Cuidá el food cost esta semana."))
    summary = await synth.synthesize(kpis=None, narrated=narrated)  # type: ignore[arg-type]
    assert summary == "Cuidá el food cost esta semana."
