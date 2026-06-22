from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class QueryResult:
    """A read-only query result: column names + rows of JSON-serializable values."""

    columns: list[str]
    rows: list[list[object]]


class CopilotLLM(ABC):
    @abstractmethod
    async def to_sql(self, question: str, schema_doc: str) -> str: ...

    @abstractmethod
    async def answer(self, question: str, result: QueryResult) -> str: ...


class CopilotQueryRunner(ABC):
    """Executes an already-validated SQL read-only, scoped to ``tenant_id`` (RLS)."""

    @abstractmethod
    async def run(self, tenant_id: str, sql: str) -> QueryResult: ...
