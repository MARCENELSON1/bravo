"""Dependency-injection container: wires domain ports to concrete adapters.

Services are singletons; repositories and use cases are factories (per use).
Tests override providers with fakes via ``container.<provider>.override(...)``.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from app.application.identity.accept_invitation import AcceptInvitation
from app.application.identity.authenticate import Authenticate
from app.application.identity.change_password import ChangePassword
from app.application.identity.invite_user import InviteUser
from app.application.identity.logout import Logout
from app.application.identity.onboard_tenant import OnboardTenant
from app.application.identity.refresh_token import RefreshAccessToken
from app.application.identity.request_password_reset import RequestPasswordReset
from app.application.identity.reset_password import ResetPassword
from app.application.identity.verify_email import VerifyEmail
from app.config import Settings
from app.infrastructure.email.console_sender import ConsoleEmailSender
from app.infrastructure.email.smtp_sender import SmtpEmailSender
from app.infrastructure.persistence.audit_repo import SqlAlchemyAuditRepository
from app.infrastructure.persistence.database import Database
from app.infrastructure.persistence.invitation_repo import SqlAlchemyInvitationRepository
from app.infrastructure.persistence.refresh_token_repo import SqlAlchemyRefreshTokenRepository
from app.infrastructure.persistence.reset_token_repo import SqlAlchemyResetTokenRepository
from app.infrastructure.persistence.tenant_repo import SqlAlchemyTenantRepository
from app.infrastructure.persistence.user_repo import SqlAlchemyUserRepository
from app.infrastructure.persistence.verification_token_repo import (
    SqlAlchemyVerificationTokenRepository,
)
from app.infrastructure.security.hasher import Argon2Hasher
from app.infrastructure.security.tenant_context import ContextVarTenantContext
from app.infrastructure.security.token_service import JwtTokenService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["app.presentation"])

    config = providers.Singleton(Settings)
    db = providers.Singleton(Database, url=config.provided.database_url)

    # --- external services (singletons) ---
    password_hasher = providers.Singleton(Argon2Hasher)
    token_service = providers.Singleton(
        JwtTokenService,
        secret=config.provided.jwt_secret,
        algorithm=config.provided.jwt_alg,
        access_token_ttl_min=config.provided.access_token_ttl_min,
    )
    tenant_context = providers.Singleton(ContextVarTenantContext)
    email_sender = providers.Selector(
        config.provided.email_transport,
        console=providers.Singleton(ConsoleEmailSender),
        smtp=providers.Singleton(
            SmtpEmailSender,
            host=config.provided.smtp_host,
            port=config.provided.smtp_port,
            username=config.provided.smtp_user,
            password=config.provided.smtp_password,
            from_email=config.provided.from_email,
            use_tls=config.provided.smtp_use_tls,
        ),
    )

    # --- repositories (per-use factories) ---
    tenant_repository = providers.Factory(
        SqlAlchemyTenantRepository, session_factory=db.provided.session
    )
    user_repository = providers.Factory(
        SqlAlchemyUserRepository, session_factory=db.provided.session
    )
    refresh_token_repository = providers.Factory(
        SqlAlchemyRefreshTokenRepository, session_factory=db.provided.session
    )
    reset_token_repository = providers.Factory(
        SqlAlchemyResetTokenRepository, session_factory=db.provided.session
    )
    verification_token_repository = providers.Factory(
        SqlAlchemyVerificationTokenRepository, session_factory=db.provided.session
    )
    invitation_repository = providers.Factory(
        SqlAlchemyInvitationRepository, session_factory=db.provided.session
    )
    audit_repository = providers.Factory(
        SqlAlchemyAuditRepository, session_factory=db.provided.session
    )

    # --- use cases (per-use factories) ---
    authenticate = providers.Factory(
        Authenticate,
        users=user_repository,
        tenants=tenant_repository,
        hasher=password_hasher,
        tokens=token_service,
        refresh_tokens=refresh_token_repository,
        audit=audit_repository,
        tenant_context=tenant_context,
        max_login_attempts=config.provided.max_login_attempts,
        lockout_minutes=config.provided.lockout_minutes,
        refresh_token_ttl_days=config.provided.refresh_token_ttl_days,
    )
    refresh_access_token = providers.Factory(
        RefreshAccessToken,
        refresh_tokens=refresh_token_repository,
        users=user_repository,
        tokens=token_service,
        audit=audit_repository,
        tenant_context=tenant_context,
        refresh_token_ttl_days=config.provided.refresh_token_ttl_days,
    )
    logout = providers.Factory(
        Logout,
        refresh_tokens=refresh_token_repository,
        tokens=token_service,
        audit=audit_repository,
        tenant_context=tenant_context,
    )
    change_password = providers.Factory(
        ChangePassword,
        users=user_repository,
        hasher=password_hasher,
        refresh_tokens=refresh_token_repository,
        audit=audit_repository,
        tenant_context=tenant_context,
    )
    request_password_reset = providers.Factory(
        RequestPasswordReset,
        tenants=tenant_repository,
        users=user_repository,
        reset_tokens=reset_token_repository,
        tokens=token_service,
        email_sender=email_sender,
        tenant_context=tenant_context,
        reset_token_ttl_min=config.provided.reset_token_ttl_min,
        app_base_url=config.provided.app_base_url,
    )
    reset_password = providers.Factory(
        ResetPassword,
        reset_tokens=reset_token_repository,
        users=user_repository,
        hasher=password_hasher,
        tokens=token_service,
        refresh_tokens=refresh_token_repository,
        audit=audit_repository,
        tenant_context=tenant_context,
    )
    verify_email = providers.Factory(
        VerifyEmail,
        verification_tokens=verification_token_repository,
        users=user_repository,
        tokens=token_service,
        audit=audit_repository,
        tenant_context=tenant_context,
    )
    onboard_tenant = providers.Factory(
        OnboardTenant,
        tenants=tenant_repository,
        users=user_repository,
        verification_tokens=verification_token_repository,
        hasher=password_hasher,
        tokens=token_service,
        email_sender=email_sender,
        audit=audit_repository,
        tenant_context=tenant_context,
        verification_token_ttl_hours=config.provided.verification_token_ttl_hours,
        app_base_url=config.provided.app_base_url,
    )
    invite_user = providers.Factory(
        InviteUser,
        users=user_repository,
        invitations=invitation_repository,
        tenants=tenant_repository,
        tokens=token_service,
        email_sender=email_sender,
        audit=audit_repository,
        tenant_context=tenant_context,
        invitation_token_ttl_hours=config.provided.invitation_token_ttl_hours,
        app_base_url=config.provided.app_base_url,
    )
    accept_invitation = providers.Factory(
        AcceptInvitation,
        invitations=invitation_repository,
        users=user_repository,
        hasher=password_hasher,
        tokens=token_service,
        audit=audit_repository,
        tenant_context=tenant_context,
    )
