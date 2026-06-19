from __future__ import annotations

from uuid import uuid4

from app.application.clock import utcnow
from app.domain.identity.exceptions import ExpiredToken, InvalidToken, TokenAlreadyUsed
from app.domain.identity.ports import (
    AuditRepository,
    TenantContext,
    TokenService,
    VerificationTokenRepository,
)
from app.domain.identity.tokens import AuthAuditEntry, AuthEvent
from app.domain.user.repository import UserRepository


class VerifyEmail:
    """Mark a user's email as verified from a single-use token."""

    def __init__(
        self,
        verification_tokens: VerificationTokenRepository,
        users: UserRepository,
        tokens: TokenService,
        audit: AuditRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._verification_tokens = verification_tokens
        self._users = users
        self._tokens = tokens
        self._audit = audit
        self._tenant_context = tenant_context

    async def execute(self, *, token: str) -> None:
        self._tokens.read_tenant(token)  # validate token format early
        record = await self._verification_tokens.get_by_hash(self._tokens.hash_token(token))
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
        user.mark_email_verified()
        await self._users.save(user)
        await self._verification_tokens.mark_used(record.id)
        await self._audit.record(
            AuthAuditEntry(
                id=str(uuid4()),
                tenant_id=tenant_id,
                event=AuthEvent.EMAIL_VERIFIED,
                user_id=user.id,
            )
        )
