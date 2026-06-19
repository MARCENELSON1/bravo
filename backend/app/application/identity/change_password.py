from __future__ import annotations

from uuid import uuid4

from app.application.clock import utcnow
from app.domain.identity.ports import (
    AuditRepository,
    PasswordHasher,
    RefreshTokenRepository,
    TenantContext,
)
from app.domain.identity.tokens import AuthAuditEntry, AuthEvent
from app.domain.user.exceptions import InvalidCredentials, UserNotFound
from app.domain.user.repository import UserRepository


class ChangePassword:
    """Change the password of an authenticated user and revoke their sessions."""

    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        refresh_tokens: RefreshTokenRepository,
        audit: AuditRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._refresh_tokens = refresh_tokens
        self._audit = audit
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, user_id: str, current_password: str, new_password: str
    ) -> None:
        self._tenant_context.set(tenant_id)
        user = await self._users.get_by_id(tenant_id, user_id)
        if user is None:
            raise UserNotFound()
        if not user.password_hash or not self._hasher.verify(current_password, user.password_hash):
            raise InvalidCredentials()
        # Defence in depth: a live access token should belong to an eligible user.
        user.can_login(utcnow())
        user.set_password(self._hasher.hash(new_password))
        await self._users.save(user)
        await self._refresh_tokens.revoke_all_for_user(tenant_id, user_id)
        await self._audit.record(
            AuthAuditEntry(
                id=str(uuid4()),
                tenant_id=tenant_id,
                event=AuthEvent.PASSWORD_CHANGED,
                user_id=user_id,
            )
        )
