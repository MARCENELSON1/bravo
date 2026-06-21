from __future__ import annotations

from pydantic import BaseModel


class ConnectUrlResponse(BaseModel):
    url: str


class MpConnectionResponse(BaseModel):
    connected: bool
    nickname: str | None = None
    external_account_id: str | None = None
    live_mode: bool = False
