from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from app.application.clock import utcnow
from app.domain.identity.ports import (
    EmailSender,
    ResetTokenRepository,
    TenantContext,
    TokenService,
)
from app.domain.identity.tokens import PasswordResetToken
from app.domain.tenant.repository import TenantRepository
from app.domain.user.repository import UserRepository


class RequestPasswordReset:
    """Start a password reset. Always neutral (no user enumeration)."""

    def __init__(
        self,
        tenants: TenantRepository,
        users: UserRepository,
        reset_tokens: ResetTokenRepository,
        tokens: TokenService,
        email_sender: EmailSender,
        tenant_context: TenantContext,
        reset_token_ttl_min: int,
        app_base_url: str,
    ) -> None:
        self._tenants = tenants
        self._users = users
        self._reset_tokens = reset_tokens
        self._tokens = tokens
        self._email_sender = email_sender
        self._tenant_context = tenant_context
        self._reset_token_ttl_min = reset_token_ttl_min
        self._app_base_url = app_base_url

    async def execute(self, *, tenant_slug: str, email: str) -> None:
        tenant = await self._tenants.get_by_slug(tenant_slug.strip().lower())
        if tenant is None:
            return
        self._tenant_context.set(tenant.id)
        user = await self._users.get_by_email(tenant.id, email.strip().lower())
        if user is None:
            return
        now = utcnow()
        # Invalidate any earlier outstanding reset tokens for this user so only the
        # newest link is ever valid.
        await self._reset_tokens.invalidate_for_user(tenant.id, user.id)
        raw = self._tokens.generate_opaque_token(tenant.id)
        await self._reset_tokens.add(
            PasswordResetToken(
                id=str(uuid4()),
                tenant_id=tenant.id,
                user_id=user.id,
                token_hash=self._tokens.hash_token(raw),
                expires_at=now + timedelta(minutes=self._reset_token_ttl_min),
            )
        )
        link = f"{self._app_base_url}/reset-password?token={raw}"
        await self._email_sender.send_password_reset(to=str(user.email), link=link)
