"""Ports for the (optional) LLM layer. The narrator turns a structured insight
into Spanish text; the synthesizer writes an overall summary. Default adapters
are deterministic (templates / none); Claude adapters sit behind a Selector and
are off by default — and never compute or invent numbers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.advisor.insights import Insight
from app.domain.advisor.kpis import AdvisorKpis


@dataclass(frozen=True)
class NarratedInsight:
    """An insight phrased for the UI. Numbers come from the structured insight,
    never recomputed: the narrator only chooses the words."""

    code: str
    severity: str
    bucket: str
    title: str
    body: str
    action: str


class InsightNarrator(ABC):
    @abstractmethod
    async def narrate(self, insight: Insight) -> NarratedInsight: ...


class AdvisorSynthesizer(ABC):
    @abstractmethod
    async def synthesize(
        self, kpis: AdvisorKpis, narrated: list[NarratedInsight]
    ) -> str | None: ...
