from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AskCopilotRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class CopilotAnswerResponse(BaseModel):
    answer: str
    sql: str  # la consulta ejecutada (fuente / transparencia)
    columns: list[str]
    rows: list[list[Any]]
    llm_enabled: bool
