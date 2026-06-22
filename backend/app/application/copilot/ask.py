"""Ask the copilot: NL question → LLM SQL → validate (guardrail) → run read-only
+ tenant-RLS → LLM answer (grounded). The numbers always come from the DB."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.copilot.exceptions import CopilotDisabled
from app.domain.copilot.ports import CopilotLLM, CopilotQueryRunner
from app.domain.copilot.schema import schema_doc
from app.domain.copilot.sql_guard import validate_sql
from app.domain.identity.ports import TenantContext


@dataclass(frozen=True)
class CopilotAnswer:
    answer: str
    sql: str
    columns: list[str]
    rows: list[list[object]]
    llm_enabled: bool


class AskCopilot:
    def __init__(
        self,
        llm: CopilotLLM,
        runner: CopilotQueryRunner,
        tenant_context: TenantContext,
        max_rows: int = 200,
        enabled: bool = False,
    ) -> None:
        self._llm = llm
        self._runner = runner
        self._tenant_context = tenant_context
        self._max_rows = max_rows
        self._enabled = enabled

    async def execute(self, *, tenant_id: str, question: str) -> CopilotAnswer:
        self._tenant_context.set(tenant_id)
        if not self._enabled:
            raise CopilotDisabled()
        raw_sql = await self._llm.to_sql(question, schema_doc())
        validated = validate_sql(raw_sql, max_rows=self._max_rows)
        result = await self._runner.run(tenant_id, validated.sql)
        answer = await self._llm.answer(question, result)
        return CopilotAnswer(
            answer=answer,
            sql=validated.sql,
            columns=result.columns,
            rows=result.rows,
            llm_enabled=True,
        )
