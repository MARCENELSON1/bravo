from __future__ import annotations

from pydantic import BaseModel, Field


class TaxJarConnectRequest(BaseModel):
    api_token: str = Field(min_length=8)
    sandbox: bool = True  # False = cuenta productiva (AutoFile real)


class TaxJarConnectionResponse(BaseModel):
    connected: bool
    sandbox: bool | None = None  # None cuando no está conectado
