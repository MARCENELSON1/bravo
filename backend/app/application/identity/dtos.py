from __future__ import annotations

from dataclasses import dataclass

from app.domain.user.value_objects import Role


@dataclass(frozen=True)
class AuthTokens:
    """Output of login/refresh: a short-lived access JWT + opaque refresh token."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass(frozen=True)
class OnboardTenantInput:
    tenant_name: str
    tenant_slug: str
    owner_email: str
    owner_password: str
    owner_name: str | None = None


@dataclass(frozen=True)
class OnboardTenantResult:
    tenant_id: str
    user_id: str


@dataclass(frozen=True)
class InviteUserInput:
    email: str
    role: Role
