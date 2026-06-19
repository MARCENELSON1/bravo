from __future__ import annotations

from uuid import uuid4

from app.application.clock import utcnow
from app.domain.identity.exceptions import InvalidInvitation
from app.domain.identity.ports import (
    AuditRepository,
    InvitationRepository,
    PasswordHasher,
    TenantContext,
    TokenService,
)
from app.domain.identity.tokens import AuthAuditEntry, AuthEvent
from app.domain.user.repository import UserRepository


class AcceptInvitation:
    """Accept an invitation: set the password, activate and verify the user."""

    def __init__(
        self,
        invitations: InvitationRepository,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
        audit: AuditRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._invitations = invitations
        self._users = users
        self._hasher = hasher
        self._tokens = tokens
        self._audit = audit
        self._tenant_context = tenant_context

    async def execute(self, *, token: str, password: str) -> None:
        self._tokens.read_tenant(token)  # validate token format early
        record = await self._invitations.get_by_hash(self._tokens.hash_token(token))
        if record is None:
            raise InvalidInvitation()
        if not record.is_valid(utcnow()):
            raise InvalidInvitation()
        tenant_id = record.tenant_id
        self._tenant_context.set(tenant_id)
        user = await self._users.get_by_id(tenant_id, record.user_id)
        if user is None:
            raise InvalidInvitation()
        user.set_password(self._hasher.hash(password))
        user.activate()
        user.mark_email_verified()
        await self._users.save(user)
        await self._invitations.mark_used(record.id)
        await self._audit.record(
            AuthAuditEntry(
                id=str(uuid4()),
                tenant_id=tenant_id,
                event=AuthEvent.INVITATION_ACCEPTED,
                user_id=user.id,
            )
        )
