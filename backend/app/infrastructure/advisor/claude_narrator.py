"""LLM narrator: Claude re-words a deterministic insight. The numbers always
come from the grounded template text; a guardrail rejects any output that
introduces a number not already present, falling back to the template."""

from __future__ import annotations

import re

from app.domain.advisor.insights import Insight
from app.domain.advisor.ports import InsightNarrator, NarratedInsight
from app.infrastructure.advisor.llm import AdvisorLLMClient

_SYSTEM = (
    "Sos un asesor financiero de un restaurante argentino. Reescribís un insight "
    "en español rioplatense, cálido y directo, en una o dos frases. REGLAS: no "
    "inventes ni calcules números — usá SOLO los que aparecen en el texto base; "
    "no agregues cifras nuevas. Devolvé solo el texto, sin encabezados."
)


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+", text))


class ClaudeNarrator(InsightNarrator):
    def __init__(self, llm: AdvisorLLMClient, fallback: InsightNarrator) -> None:
        self._llm = llm
        self._fallback = fallback

    async def narrate(self, insight: Insight) -> NarratedInsight:
        template = await self._fallback.narrate(insight)
        base = f"{template.title}. {template.body} {template.action}"
        try:
            text = (await self._llm.complete(system=_SYSTEM, user=base)).strip()
        except Exception:
            return template  # any LLM failure → deterministic fallback
        # Guardrail: reject hallucinated numbers (any digit not in the base).
        if not text or (_numbers(text) - _numbers(base)):
            return template
        return NarratedInsight(
            code=template.code,
            severity=template.severity,
            bucket=template.bucket,
            title=template.title,
            body=text,
            action=template.action,
        )
