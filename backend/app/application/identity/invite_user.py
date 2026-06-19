from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from app.application.clock import utcnow
from app.application.identity.dtos import InviteUserInput
from app.domain.identity.ports import (
    AuditRepository,
    EmailSender,
    InvitationRepository,
    TenantContext,
    TokenService,
)
from app.domain.identity.tokens import AuthAuditEntry, AuthEvent, Invitation
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.tenant.repository import TenantRepository
from app.domain.user.entities import User
from app.domain.user.exceptions import EmailAlreadyRegistered, InsufficientRole
from app.domain.user.repository import UserRepository
from app.domain.user.value_objects import Email, Role

# A role may only invite roles strictly below it (no peer/up-level invitations).
_INVITE_CEILING: dict[Role, set[Role]] = {
    Role.OWNER: {Role.MANAGER, Role.WAITER, Role.KITCHEN, Role.CASHIER},
    Role.MANAGER: {Role.WAITER, Role.KITCHEN, Role.CASHIER},
}


class InviteUser:
    """Invite a staff member: create an inactive user + send an invitation link.

    Caller authorization (OWNER/MANAGER) is enforced in the presentation layer.
    OWNER cannot be invited (owners come from onboarding) — enforced by the schema.
    """

    def __init__(
        self,
        users: UserRepository,
        invitations: InvitationRepository,
        tenants: TenantRepository,
        tokens: TokenService,
        email_sender: EmailSender,
        audit: AuditRepository,
        tenant_context: TenantContext,
        invitation_token_ttl_hours: int,
        app_base_url: str,
    ) -> None:
        self._users = users
        self._invitations = invitations
        self._tenants = tenants
        self._tokens = tokens
        self._email_sender = email_sender
        self._audit = audit
        self._tenant_context = tenant_context
        self._invitation_token_ttl_hours = invitation_token_ttl_hours
        self._app_base_url = app_base_url

    async def execute(
        self, *, tenant_id: str, invited_by: str, inviter_role: Role, data: InviteUserInput
    ) -> None:
        if data.role not in _INVITE_CEILING.get(inviter_role, set()):
            raise InsufficientRole()
        self._tenant_context.set(tenant_id)
        email = Email(data.email)
        if await self._users.get_by_email(tenant_id, email.value) is not None:
            raise EmailAlreadyRegistered()
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFound()
        now = utcnow()
        user = User(
            id=str(uuid4()),
            tenant_id=tenant_id,
            email=email,
            role=data.role,
            password_hash=None,
            email_verified=False,
            active=False,
        )
        await self._users.add(user)
        raw = self._tokens.generate_opaque_token(tenant_id)
        await self._invitations.add(
            Invitation(
                id=str(uuid4()),
                tenant_id=tenant_id,
                user_id=user.id,
                email=email.value,
                role=data.role,
                token_hash=self._tokens.hash_token(raw),
                expires_at=now + timedelta(hours=self._invitation_token_ttl_hours),
                invited_by=invited_by,
            )
        )
        link = f"{self._app_base_url}/accept-invitation?token={raw}"
        await self._email_sender.send_invitation(
            to=email.value, link=link, tenant_name=tenant.name
        )
        await self._audit.record(
            AuthAuditEntry(
                id=str(uuid4()),
                tenant_id=tenant_id,
                event=AuthEvent.USER_INVITED,
                user_id=user.id,
            )
        )
