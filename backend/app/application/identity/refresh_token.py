from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from app.application.clock import utcnow
from app.application.identity.dtos import AuthTokens
from app.domain.identity.exceptions import ExpiredToken, InvalidToken
from app.domain.identity.ports import (
    AuditRepository,
    RefreshTokenRepository,
    TenantContext,
    TokenService,
)
from app.domain.identity.tokens import AuthAuditEntry, AuthEvent, RefreshToken
from app.domain.user.repository import UserRepository


class RefreshAccessToken:
    """Rotate a refresh token: revoke the presented one and issue a fresh pair."""

    def __init__(
        self,
        refresh_tokens: RefreshTokenRepository,
        users: UserRepository,
        tokens: TokenService,
        audit: AuditRepository,
        tenant_context: TenantContext,
        refresh_token_ttl_days: int,
    ) -> None:
        self._refresh_tokens = refresh_tokens
        self._users = users
        self._tokens = tokens
        self._audit = audit
        self._tenant_context = tenant_context
        self._refresh_token_ttl_days = refresh_token_ttl_days

    async def execute(self, *, refresh_token: str) -> AuthTokens:
        self._tokens.read_tenant(refresh_token)  # validate token format early
        now = utcnow()
        record = await self._refresh_tokens.get_by_hash(self._tokens.hash_token(refresh_token))
        if record is None or record.revoked:
            raise InvalidToken()
        if record.expires_at <= now:
            raise ExpiredToken()
        # Scope RLS from the authoritative tenant on the stored record, never from
        # the (untrusted) token prefix.
        tenant_id = record.tenant_id
        self._tenant_context.set(tenant_id)
        await self._refresh_tokens.revoke(record.id)
        user = await self._users.get_by_id(tenant_id, record.user_id)
        if user is None:
            raise InvalidToken()
        access = self._tokens.create_access_token(
            user_id=user.id, tenant_id=tenant_id, role=user.role
        )
        raw_new = self._tokens.generate_opaque_token(tenant_id)
        await self._refresh_tokens.add(
            RefreshToken(
                id=str(uuid4()),
                tenant_id=tenant_id,
                user_id=user.id,
                token_hash=self._tokens.hash_token(raw_new),
                expires_at=now + timedelta(days=self._refresh_token_ttl_days),
            )
        )
        await self._audit.record(
            AuthAuditEntry(
                id=str(uuid4()),
                tenant_id=tenant_id,
                event=AuthEvent.TOKEN_REFRESHED,
                user_id=user.id,
            )
        )
        return AuthTokens(access_token=access, refresh_token=raw_new)
