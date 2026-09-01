from __future__ import annotations

from pydantic import BaseModel


class SelfOrderSettingsResponse(BaseModel):
    enabled: bool
    requires_confirmation: bool


class UpdateSelfOrderSettingsRequest(BaseModel):
    enabled: bool
    requires_confirmation: bool
