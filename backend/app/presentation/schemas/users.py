from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.domain.user.value_objects import Role


class InviteRequest(BaseModel):
    email: EmailStr
    role: Role

    @field_validator("role")
    @classmethod
    def role_cannot_be_owner(cls, value: Role) -> Role:
        if value is Role.OWNER:
            raise ValueError("No se puede invitar con el rol OWNER.")
        return value


class AcceptInvitationRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)
