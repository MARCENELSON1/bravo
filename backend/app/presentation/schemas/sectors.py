from __future__ import annotations

from pydantic import BaseModel, Field


class SectorRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    color: str | None = Field(default=None, max_length=20)
    sort_order: int = Field(default=0, ge=0)


class SectorResponse(BaseModel):
    id: str
    name: str
    color: str | None = None
    sort_order: int = 0
