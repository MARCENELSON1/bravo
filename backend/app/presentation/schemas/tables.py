from __future__ import annotations

from pydantic import BaseModel, Field


class CreateTableRequest(BaseModel):
    number: int = Field(ge=0)
    name: str | None = Field(default=None, max_length=120)


class CreateTableResponse(BaseModel):
    table_id: str


class TableResponse(BaseModel):
    id: str
    number: int
    name: str | None
    active: bool
