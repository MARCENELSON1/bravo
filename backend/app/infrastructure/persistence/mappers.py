"""Mappers between ORM models and domain entities.

``*_to_orm`` omits ``created_at`` so that ``session.merge`` (updates) never
clobbers the DB-managed timestamp and inserts use the column ``server_default``.
"""

from __future__ import annotations

from app.domain.identity.tokens import (
    AuthAuditEntry,
    AuthEvent,
    EmailVerificationToken,
    Invitation,
    PasswordResetToken,
    RefreshToken,
)
from app.domain.tenant.entities import Tenant
from app.domain.user.entities import User
from app.domain.user.value_objects import Email, Role
from app.infrastructure.persistence.models import (
    AuthAuditORM,
    EmailVerificationTokenORM,
    InvitationORM,
    PasswordResetTokenORM,
    RefreshTokenORM,
    TenantORM,
    UserORM,
)

# --- Tenant ---------------------------------------------------------------


def tenant_to_domain(row: TenantORM) -> Tenant:
    return Tenant(id=row.id, slug=row.slug, name=row.name, created_at=row.created_at)


def tenant_to_orm(tenant: Tenant) -> TenantORM:
    return TenantORM(id=tenant.id, slug=tenant.slug, name=tenant.name)


# --- User -----------------------------------------------------------------


def user_to_domain(row: UserORM) -> User:
    return User(
        id=row.id,
        tenant_id=row.tenant_id,
        email=Email(row.email),
        role=Role(row.role),
        password_hash=row.password_hash,
        email_verified=row.email_verified,
        active=row.active,
        failed_attempts=row.failed_attempts,
        locked_until=row.locked_until,
        created_at=row.created_at,
    )


def user_to_orm(user: User) -> UserORM:
    return UserORM(
        id=user.id,
        tenant_id=user.tenant_id,
        email=str(user.email),
        role=user.role.value,
        password_hash=user.password_hash,
        email_verified=user.email_verified,
        active=user.active,
        failed_attempts=user.failed_attempts,
        locked_until=user.locked_until,
    )


# --- Refresh token --------------------------------------------------------


def refresh_token_to_domain(row: RefreshTokenORM) -> RefreshToken:
    return RefreshToken(
        id=row.id,
        tenant_id=row.tenant_id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        revoked=row.revoked,
        created_at=row.created_at,
    )


def refresh_token_to_orm(token: RefreshToken) -> RefreshTokenORM:
    return RefreshTokenORM(
        id=token.id,
        tenant_id=token.tenant_id,
        user_id=token.user_id,
        token_hash=token.token_hash,
        expires_at=token.expires_at,
        revoked=token.revoked,
    )


# --- Password reset token -------------------------------------------------


def reset_token_to_domain(row: PasswordResetTokenORM) -> PasswordResetToken:
    return PasswordResetToken(
        id=row.id,
        tenant_id=row.tenant_id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        used=row.used,
        created_at=row.created_at,
    )


def reset_token_to_orm(token: PasswordResetToken) -> PasswordResetTokenORM:
    return PasswordResetTokenORM(
        id=token.id,
        tenant_id=token.tenant_id,
        user_id=token.user_id,
        token_hash=token.token_hash,
        expires_at=token.expires_at,
        used=token.used,
    )


# --- Email verification token ---------------------------------------------


def verification_token_to_domain(row: EmailVerificationTokenORM) -> EmailVerificationToken:
    return EmailVerificationToken(
        id=row.id,
        tenant_id=row.tenant_id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        used=row.used,
        created_at=row.created_at,
    )


def verification_token_to_orm(token: EmailVerificationToken) -> EmailVerificationTokenORM:
    return EmailVerificationTokenORM(
        id=token.id,
        tenant_id=token.tenant_id,
        user_id=token.user_id,
        token_hash=token.token_hash,
        expires_at=token.expires_at,
        used=token.used,
    )


# --- Invitation -----------------------------------------------------------


def invitation_to_domain(row: InvitationORM) -> Invitation:
    return Invitation(
        id=row.id,
        tenant_id=row.tenant_id,
        user_id=row.user_id,
        email=row.email,
        role=Role(row.role),
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        invited_by=row.invited_by,
        used=row.used,
        created_at=row.created_at,
    )


def invitation_to_orm(invitation: Invitation) -> InvitationORM:
    return InvitationORM(
        id=invitation.id,
        tenant_id=invitation.tenant_id,
        user_id=invitation.user_id,
        email=invitation.email,
        role=invitation.role.value,
        token_hash=invitation.token_hash,
        expires_at=invitation.expires_at,
        used=invitation.used,
        invited_by=invitation.invited_by,
    )


# --- Audit ----------------------------------------------------------------


def audit_to_orm(entry: AuthAuditEntry) -> AuthAuditORM:
    return AuthAuditORM(
        id=entry.id,
        tenant_id=entry.tenant_id,
        user_id=entry.user_id,
        event=str(entry.event),
        detail=entry.detail,
    )


def audit_to_domain(row: AuthAuditORM) -> AuthAuditEntry:
    return AuthAuditEntry(
        id=row.id,
        tenant_id=row.tenant_id,
        event=AuthEvent(row.event),
        user_id=row.user_id,
        detail=row.detail,
        created_at=row.created_at,
    )
