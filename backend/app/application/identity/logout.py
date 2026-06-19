from __future__ import annotations

from uuid import uuid4

from app.domain.identity.exceptions import InvalidToken
from app.domain.identity.ports import (
    AuditRepository,
    RefreshTokenRepository,
    TenantContext,
    TokenService,
)
from app.domain.identity.tokens import AuthAuditEntry, AuthEvent


class Logout:
    """Revoke a refresh token (server-side logout). Idempotent and neutral."""

    def __init__(
        self,
        refresh_tokens: RefreshTokenRepository,
        tokens: TokenService,
        audit: AuditRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._refresh_tokens = refresh_tokens
        self._tokens = tokens
        self._audit = audit
        self._tenant_context = tenant_context

    async def execute(self, *, refresh_token: str) -> None:
        try:
            self._tokens.read_tenant(refresh_token)  # validate token format early
        except InvalidToken:
            return
        record = await self._refresh_tokens.get_by_hash(self._tokens.hash_token(refresh_token))
        if record is not None and not record.revoked:
            self._tenant_context.set(record.tenant_id)
            await self._refresh_tokens.revoke(record.id)
            await self._audit.record(
                AuthAuditEntry(
                    id=str(uuid4()),
                    tenant_id=record.tenant_id,
                    event=AuthEvent.LOGOUT,
                    user_id=record.user_id,
                )
            )
