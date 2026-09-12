from __future__ import annotations

from pydantic import BaseModel


class SelfPaySettingsResponse(BaseModel):
    enabled: bool
    tips_enabled: bool


class UpdateSelfPaySettingsRequest(BaseModel):
    enabled: bool
    tips_enabled: bool
