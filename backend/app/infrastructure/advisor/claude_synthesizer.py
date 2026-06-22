"""LLM synthesizer: Claude writes a 1–2 sentence summary over the period's
insights. Same guardrail — only numbers already present in the insights survive,
otherwise no summary is returned."""

from __future__ import annotations

import re

from app.domain.advisor.kpis import AdvisorKpis
from app.domain.advisor.ports import AdvisorSynthesizer, NarratedInsight
from app.infrastructure.advisor.llm import AdvisorLLMClient

_SYSTEM = (
    "Sos un asesor financiero de un restaurante argentino. A partir de los "
    "insights del período, escribí un resumen de una o dos frases en español "
    "rioplatense con UNA acción concreta. No inventes ni calcules números: usá "
    "SOLO los que aparecen en los insights. Si no hay nada relevante, respondé 'OK'."
)


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+", text))


class ClaudeSynthesizer(AdvisorSynthesizer):
    def __init__(self, llm: AdvisorLLMClient) -> None:
        self._llm = llm

    async def synthesize(
        self, kpis: AdvisorKpis, narrated: list[NarratedInsight]
    ) -> str | None:
        if not narrated:
            return None
        base = " ".join(f"{n.title}. {n.body} {n.action}" for n in narrated)
        try:
            text = (await self._llm.complete(system=_SYSTEM, user=base)).strip()
        except Exception:
            return None
        if not text or text == "OK" or (_numbers(text) - _numbers(base)):
            return None
        return text
