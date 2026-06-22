"""Thin LLM client port + Anthropic adapter. Kept minimal so the narrator/
synthesizer depend on an interface (and tests inject a fake — no network)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AdvisorLLMClient(ABC):
    @abstractmethod
    async def complete(self, *, system: str, user: str) -> str: ...


class AnthropicAdvisorLLM(AdvisorLLMClient):
    """Anthropic (Claude) adapter. ``anthropic`` is imported lazily so the
    dependency is only required when ``advisor_llm_provider=claude`` (off by
    default). Never used in tests (a fake client is injected)."""

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._client: Any = None

    async def complete(self, *, system: str, user: str) -> str:
        if self._client is None:
            import anthropic  # type: ignore[import-not-found]

            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
        message = await self._client.messages.create(
            model=self._model,
            max_tokens=300,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        parts = [
            block.text
            for block in message.content
            if getattr(block, "type", None) == "text"
        ]
        return "".join(parts).strip()
