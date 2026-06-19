from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from app.application.clock import utcnow
from app.application.identity.dtos import OnboardTenantInput, OnboardTenantResult
from app.domain.identity.ports import (
    AuditRepository,
    EmailSender,
    PasswordHasher,
    TenantContext,
    TokenService,
    VerificationTokenRepository,
)
from app.domain.identity.tokens import AuthAuditEntry, AuthEvent, EmailVerificationToken
from app.domain.tenant.entities import Tenant
from app.domain.tenant.exceptions import TenantAlreadyExists
from app.domain.tenant.repository import TenantRepository
from app.domain.user.entities import User
from app.domain.user.repository import UserRepository
from app.domain.user.value_objects import Email, Role


class OnboardTenant:
    """Create a new tenant with its OWNER user and send email verification."""

    def __init__(
        self,
        tenants: TenantRepository,
        users: UserRepository,
        verification_tokens: VerificationTokenRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
        email_sender: EmailSender,
        audit: AuditRepository,
        tenant_context: TenantContext,
        verification_token_ttl_hours: int,
        app_base_url: str,
    ) -> None:
        self._tenants = tenants
        self._users = users
        self._verification_tokens = verification_tokens
        self._hasher = hasher
        self._tokens = tokens
        self._email_sender = email_sender
        self._audit = audit
        self._tenant_context = tenant_context
        self._verification_token_ttl_hours = verification_token_ttl_hours
        self._app_base_url = app_base_url

    async def execute(self, data: OnboardTenantInput) -> OnboardTenantResult:
        slug = data.tenant_slug.strip().lower()
        if await self._tenants.get_by_slug(slug) is not None:
            raise TenantAlreadyExists()
        email = Email(data.owner_email)  # validates format → InvalidEmail on bad input
        tenant = Tenant(id=str(uuid4()), slug=slug, name=data.tenant_name.strip())
        await self._tenants.add(tenant)
        self._tenant_context.set(tenant.id)
        now = utcnow()
        user = User(
            id=str(uuid4()),
            tenant_id=tenant.id,
            email=email,
            role=Role.OWNER,
            password_hash=self._hasher.hash(data.owner_password),
            email_verified=False,
            active=True,
        )
        await self._users.add(user)
        raw = self._tokens.generate_opaque_token(tenant.id)
        await self._verification_tokens.add(
            EmailVerificationToken(
                id=str(uuid4()),
                tenant_id=tenant.id,
                user_id=user.id,
                token_hash=self._tokens.hash_token(raw),
                expires_at=now + timedelta(hours=self._verification_token_ttl_hours),
            )
        )
        link = f"{self._app_base_url}/verify-email?token={raw}"
        await self._email_sender.send_email_verification(to=str(user.email), link=link)
        await self._audit.record(
            AuthAuditEntry(
                id=str(uuid4()),
                tenant_id=tenant.id,
                event=AuthEvent.TENANT_ONBOARDED,
                user_id=user.id,
            )
        )
        return OnboardTenantResult(tenant_id=tenant.id, user_id=user.id)
