from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class AccessTokenResponse(BaseModel):
    # The refresh token is NOT in the body: it travels in an HttpOnly cookie.
    access_token: str
    token_type: str = "bearer"


# Body is optional: browsers send the refresh token via the HttpOnly cookie.
# The optional field is a fallback for non-browser clients and tests.
class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    tenant_slug: str = Field(min_length=2, max_length=63)
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str


class MessageResponse(BaseModel):
    message: str


class PingResponse(BaseModel):
    tenant_id: str
    user_id: str
    role: str
