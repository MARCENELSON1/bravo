from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class OnboardingRequest(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=120)
    tenant_slug: str = Field(min_length=2, max_length=63, pattern=r"^[a-z0-9-]+$")
    owner_email: EmailStr
    owner_password: str = Field(min_length=8, max_length=128)
    owner_name: str | None = Field(default=None, max_length=120)


class OnboardingResponse(BaseModel):
    tenant_id: str
    user_id: str
    message: str
