from __future__ import annotations

from uuid import uuid4

from app.application.clock import utcnow
from app.domain.identity.exceptions import ExpiredToken, InvalidToken, TokenAlreadyUsed
from app.domain.identity.ports import (
    AuditRepository,
    PasswordHasher,
    RefreshTokenRepository,
    ResetTokenRepository,
    TenantContext,
    TokenService,
)
from app.domain.identity.tokens import AuthAuditEntry, AuthEvent
from app.domain.user.repository import UserRepository


class ResetPassword:
    """Complete a password reset using a single-use, hashed, expiring token."""

    def __init__(
        self,
        reset_tokens: ResetTokenRepository,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
        refresh_tokens: RefreshTokenRepository,
        audit: AuditRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._reset_tokens = reset_tokens
        self._users = users
        self._hasher = hasher
        self._tokens = tokens
        self._refresh_tokens = refresh_tokens
        self._audit = audit
        self._tenant_context = tenant_context

    async def execute(self, *, token: str, new_password: str) -> None:
        self._tokens.read_tenant(token)  # validate token format early
        record = await self._reset_tokens.get_by_hash(self._tokens.hash_token(token))
        if record is None:
            raise InvalidToken()
        now = utcnow()
        if record.used:
            raise TokenAlreadyUsed()
        if record.expires_at <= now:
            raise ExpiredToken()
        tenant_id = record.tenant_id
        self._tenant_context.set(tenant_id)
        user = await self._users.get_by_id(tenant_id, record.user_id)
        if user is None:
            raise InvalidToken()
        user.set_password(self._hasher.hash(new_password))
        await self._users.save(user)
        await self._reset_tokens.mark_used(record.id)
        await self._refresh_tokens.revoke_all_for_user(tenant_id, user.id)
        await self._audit.record(
            AuthAuditEntry(
                id=str(uuid4()),
                tenant_id=tenant_id,
                event=AuthEvent.PASSWORD_RESET,
                user_id=user.id,
            )
        )
