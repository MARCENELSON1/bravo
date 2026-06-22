"""Shared low-level LLM client port + Anthropic adapter. Reused by the copilot
(Fase 11). The advisor (Fase 9) keeps its own copy to avoid churn; consolidating
both onto this client is a deferred cleanup."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LlmClient(ABC):
    @abstractmethod
    async def complete(self, *, system: str, user: str, max_tokens: int = 512) -> str: ...


class AnthropicClient(LlmClient):
    """``anthropic`` is imported lazily; only constructed when the provider is on."""

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._client: Any = None

    async def complete(self, *, system: str, user: str, max_tokens: int = 512) -> str:
        if self._client is None:
            import anthropic  # type: ignore[import-not-found]

            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
        message = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        parts = [
            block.text
            for block in message.content
            if getattr(block, "type", None) == "text"
        ]
        return "".join(parts).strip()
