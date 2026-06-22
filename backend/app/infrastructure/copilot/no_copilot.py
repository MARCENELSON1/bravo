"""Disabled copilot (provider=off): every call raises ``CopilotDisabled``."""

from __future__ import annotations

from app.domain.copilot.exceptions import CopilotDisabled
from app.domain.copilot.ports import CopilotLLM, QueryResult


class NoCopilot(CopilotLLM):
    async def to_sql(self, question: str, schema_doc: str) -> str:
        raise CopilotDisabled()

    async def answer(self, question: str, result: QueryResult) -> str:
        raise CopilotDisabled()
