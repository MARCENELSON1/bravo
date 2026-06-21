from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ShiftResponse(BaseModel):
    id: str
    user_id: str
    clock_in_at: datetime
    clock_out_at: datetime | None
    status: str
    source: str
    worked_minutes: int | None
    note: str | None
    adjusted_by: str | None


class MyTimeclockResponse(BaseModel):
    open_shift: ShiftResponse | None
    recent: list[ShiftResponse]


class ClockInRequest(BaseModel):
    note: str | None = None


class AdjustShiftRequest(BaseModel):
    clock_in_at: datetime
    clock_out_at: datetime | None = None


# --- Presence layer (Fase 5.5) ---


class PresenceChallengeResponse(BaseModel):
    qr_payload: str
    code: str
    expires_at: datetime


class PresenceDeviceResponse(BaseModel):
    device_token: str


class PresencePunchRequest(BaseModel):
    presented: str
