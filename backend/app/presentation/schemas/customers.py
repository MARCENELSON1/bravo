from __future__ import annotations

from pydantic import BaseModel, Field


class CustomerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=500)
    no_contactar: bool = False


class CustomerResponse(BaseModel):
    id: str
    name: str
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    no_contactar: bool = False
