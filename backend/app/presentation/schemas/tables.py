from __future__ import annotations

from pydantic import BaseModel, Field


class CreateTableRequest(BaseModel):
    number: int = Field(ge=0)
    name: str | None = Field(default=None, max_length=120)


class CreateTableResponse(BaseModel):
    table_id: str


class UpdateTableRequest(BaseModel):
    # A field left out is untouched; sending null clears it (see the endpoint's
    # use of ``model_fields_set``).
    sector_id: str | None = None
    capacity: int | None = Field(default=None, ge=1)


class TableResponse(BaseModel):
    id: str
    number: int
    name: str | None
    active: bool
    sector_id: str | None = None
    capacity: int | None = None
