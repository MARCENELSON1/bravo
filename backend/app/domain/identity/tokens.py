from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.user.value_objects import Role


class AuthEvent(StrEnum):
    """Auditable authentication events."""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGIN_LOCKED = "login_locked"
    LOGOUT = "logout"
    TOKEN_REFRESHED = "token_refreshed"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFIED = "email_verified"
    TENANT_ONBOARDED = "tenant_onboarded"
    USER_INVITED = "user_invited"
    INVITATION_ACCEPTED = "invitation_accepted"


@dataclass(frozen=True)
class AccessClaims:
    """Decoded access-token claims."""

    user_id: str
    tenant_id: str
    role: Role


@dataclass
class RefreshToken:
    """Server-side refresh token (only the hash is persisted)."""

    id: str
    tenant_id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    revoked: bool = False
    created_at: datetime | None = None

    def is_active(self, now: datetime) -> bool:
        return not self.revoked and self.expires_at > now


@dataclass
class PasswordResetToken:
    id: str
    tenant_id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    used: bool = False
    created_at: datetime | None = None

    def is_valid(self, now: datetime) -> bool:
        return not self.used and self.expires_at > now


@dataclass
class EmailVerificationToken:
    id: str
    tenant_id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    used: bool = False
    created_at: datetime | None = None

    def is_valid(self, now: datetime) -> bool:
        return not self.used and self.expires_at > now


@dataclass
class Invitation:
    id: str
    tenant_id: str
    user_id: str
    email: str
    role: Role
    token_hash: str
    expires_at: datetime
    invited_by: str | None = None
    used: bool = False
    created_at: datetime | None = None

    def is_valid(self, now: datetime) -> bool:
        return not self.used and self.expires_at > now


@dataclass
class AuthAuditEntry:
    id: str
    tenant_id: str
    event: AuthEvent
    user_id: str | None = None
    detail: str | None = None
    created_at: datetime | None = None
