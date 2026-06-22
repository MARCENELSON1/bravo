"""Copilot LLM adapter with a FAKE client (no network): SQL fence-stripping and
the answer guardrail (numbers must come from the result rows)."""

from __future__ import annotations

import pytest

from app.domain.copilot.ports import QueryResult
from app.infrastructure.copilot.anthropic_copilot import AnthropicCopilotLLM
from app.infrastructure.llm.client import LlmClient

pytestmark = pytest.mark.asyncio

_RESULT = QueryResult(columns=["product_name", "total"], rows=[["Milanesa", 300000]])


class _FakeLlm(LlmClient):
    def __init__(self, reply: str | Exception) -> None:
        self._reply = reply

    async def complete(self, *, system: str, user: str, max_tokens: int = 512) -> str:
        if isinstance(self._reply, Exception):
            raise self._reply
        return self._reply


async def test_to_sql_strips_markdown_fences() -> None:
    llm = _FakeLlm("```sql\nSELECT name FROM products\n```")
    out = await AnthropicCopilotLLM(llm).to_sql("¿qué productos?", "schema")
    assert out == "SELECT name FROM products"


async def test_answer_uses_grounded_text() -> None:
    llm = _FakeLlm("Milanesa fue lo más vendido, con 300000 en ventas.")
    out = await AnthropicCopilotLLM(llm).answer("¿qué vendí?", _RESULT)
    assert "Milanesa" in out


async def test_answer_accepts_thousands_separator() -> None:
    # "$300.000" normalizes to 300000, which IS in the rows.
    llm = _FakeLlm("Milanesa vendió $300.000.")
    out = await AnthropicCopilotLLM(llm).answer("?", _RESULT)
    assert "300.000" in out


async def test_answer_rejects_hallucinated_number() -> None:
    llm = _FakeLlm("Vendiste 999999 de Milanesa.")  # 999999 not in the rows
    out = await AnthropicCopilotLLM(llm).answer("?", _RESULT)
    assert "999999" not in out  # fell back to the deterministic count


async def test_answer_falls_back_on_error() -> None:
    out = await AnthropicCopilotLLM(_FakeLlm(RuntimeError("boom"))).answer("?", _RESULT)
    assert out  # deterministic fallback, no crash


async def test_answer_no_rows() -> None:
    empty = QueryResult(columns=["x"], rows=[])
    llm = _FakeLlm("Vendiste un montón.")
    out = await AnthropicCopilotLLM(llm).answer("?", empty)
    assert "no" in out.lower()  # "No encontré datos…"
