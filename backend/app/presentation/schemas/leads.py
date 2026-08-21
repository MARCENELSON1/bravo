from __future__ import annotations

from pydantic import BaseModel, Field


class LeadRequest(BaseModel):
    """Formulario público de la landing. Los largos acotan lo que entra sin auth."""

    email: str = Field(max_length=320)
    name: str | None = Field(default=None, max_length=200)
    message: str | None = Field(default=None, max_length=2000)


class LeadResponse(BaseModel):
    message: str
