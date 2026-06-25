"""In-memory fakes for every domain port, plus a Harness that wires use cases.

Used by unit tests (no DB, no network). The fakes intentionally keep behaviour
minimal but faithful to the port contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

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
from app.domain.identity.exceptions import InvalidToken
from app.domain.identity.ports import (
    AuditRepository,
    EmailSender,
    InvitationRepository,
    PasswordHasher,
    RefreshTokenRepository,
    ResetTokenRepository,
    TenantContext,
    TokenService,
    VerificationTokenRepository,
)
from app.domain.identity.tokens import (
    AccessClaims,
    AuthAuditEntry,
    EmailVerificationToken,
    Invitation,
    PasswordResetToken,
    RefreshToken,
)
from app.domain.tenant.entities import Tenant
from app.domain.tenant.repository import TenantRepository
from app.domain.user.entities import User
from app.domain.user.repository import UserRepository
from app.domain.user.value_objects import Role


class FakeTenantRepository(TenantRepository):
    def __init__(self) -> None:
        self.by_id: dict[str, Tenant] = {}

    async def get_by_id(self, tenant_id: str) -> Tenant | None:
        return self.by_id.get(tenant_id)

    async def get_by_slug(self, slug: str) -> Tenant | None:
        return next((t for t in self.by_id.values() if t.slug == slug), None)

    async def add(self, tenant: Tenant) -> None:
        self.by_id[tenant.id] = tenant


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self.by_id: dict[str, User] = {}

    async def get_by_id(self, tenant_id: str, user_id: str) -> User | None:
        user = self.by_id.get(user_id)
        return user if user and user.tenant_id == tenant_id else None

    async def get_by_email(self, tenant_id: str, email: str) -> User | None:
        return next(
            (u for u in self.by_id.values() if u.tenant_id == tenant_id and str(u.email) == email),
            None,
        )

    async def add(self, user: User) -> None:
        self.by_id[user.id] = user

    async def save(self, user: User) -> None:
        self.by_id[user.id] = user


class FakeRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self) -> None:
        self.items: dict[str, RefreshToken] = {}

    async def add(self, token: RefreshToken) -> None:
        self.items[token.id] = token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return next((t for t in self.items.values() if t.token_hash == token_hash), None)

    async def revoke(self, token_id: str) -> None:
        if token_id in self.items:
            self.items[token_id].revoked = True

    async def revoke_all_for_user(self, tenant_id: str, user_id: str) -> None:
        for t in self.items.values():
            if t.tenant_id == tenant_id and t.user_id == user_id:
                t.revoked = True


class FakeResetTokenRepository(ResetTokenRepository):
    def __init__(self) -> None:
        self.items: dict[str, PasswordResetToken] = {}

    async def add(self, token: PasswordResetToken) -> None:
        self.items[token.id] = token

    async def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        return next((t for t in self.items.values() if t.token_hash == token_hash), None)

    async def mark_used(self, token_id: str) -> None:
        if token_id in self.items:
            self.items[token_id].used = True

    async def invalidate_for_user(self, tenant_id: str, user_id: str) -> None:
        for token in self.items.values():
            if token.tenant_id == tenant_id and token.user_id == user_id:
                token.used = True


class FakeVerificationTokenRepository(VerificationTokenRepository):
    def __init__(self) -> None:
        self.items: dict[str, EmailVerificationToken] = {}

    async def add(self, token: EmailVerificationToken) -> None:
        self.items[token.id] = token

    async def get_by_hash(self, token_hash: str) -> EmailVerificationToken | None:
        return next((t for t in self.items.values() if t.token_hash == token_hash), None)

    async def mark_used(self, token_id: str) -> None:
        if token_id in self.items:
            self.items[token_id].used = True


class FakeInvitationRepository(InvitationRepository):
    def __init__(self) -> None:
        self.items: dict[str, Invitation] = {}

    async def add(self, invitation: Invitation) -> None:
        self.items[invitation.id] = invitation

    async def get_by_hash(self, token_hash: str) -> Invitation | None:
        return next((i for i in self.items.values() if i.token_hash == token_hash), None)

    async def mark_used(self, invitation_id: str) -> None:
        if invitation_id in self.items:
            self.items[invitation_id].used = True


class FakeAuditRepository(AuditRepository):
    def __init__(self) -> None:
        self.entries: list[AuthAuditEntry] = []

    async def record(self, entry: AuthAuditEntry) -> None:
        self.entries.append(entry)

    def events(self) -> list[str]:
        return [str(e.event) for e in self.entries]


class FakeTenantContext(TenantContext):
    def __init__(self) -> None:
        self.current: str | None = None

    def set(self, tenant_id: str) -> None:
        self.current = tenant_id

    def get(self) -> str | None:
        return self.current


class FakePasswordHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{password}"


class FakeTokenService(TokenService):
    def create_access_token(self, *, user_id: str, tenant_id: str, role: Role) -> str:
        return f"access:{tenant_id}:{user_id}:{role}"

    def decode_access_token(self, token: str) -> AccessClaims:
        try:
            _, tenant_id, user_id, role = token.split(":")
        except ValueError as exc:
            raise InvalidToken() from exc
        return AccessClaims(user_id=user_id, tenant_id=tenant_id, role=Role(role))

    def create_stream_token(self, *, tenant_id: str, ttl_seconds: int) -> str:
        return f"stream:{tenant_id}"

    def decode_stream_token(self, token: str) -> str:
        kind, _, tenant_id = token.partition(":")
        if kind != "stream" or not tenant_id:
            raise InvalidToken()
        return tenant_id

    def generate_opaque_token(self, tenant_id: str) -> str:
        return f"{tenant_id}.{uuid4().hex}"

    def read_tenant(self, token: str) -> str:
        if "." not in token:
            raise InvalidToken()
        return token.split(".", 1)[0]

    def hash_token(self, token: str) -> str:
        return f"h:{token}"

    def verify_token(self, token: str, token_hash: str) -> bool:
        return self.hash_token(token) == token_hash


@dataclass
class SentEmail:
    kind: str
    to: str
    link: str
    extra: dict[str, str] = field(default_factory=dict)


class FakeEmailSender(EmailSender):
    def __init__(self) -> None:
        self.sent: list[SentEmail] = []

    async def send_email_verification(self, *, to: str, link: str) -> None:
        self.sent.append(SentEmail("verification", to, link))

    async def send_password_reset(self, *, to: str, link: str) -> None:
        self.sent.append(SentEmail("reset", to, link))

    async def send_invitation(self, *, to: str, link: str, tenant_name: str) -> None:
        self.sent.append(SentEmail("invitation", to, link, {"tenant_name": tenant_name}))

    def last(self) -> SentEmail:
        return self.sent[-1]


@dataclass
class Harness:
    """Holds all fakes and builds use cases wired to them."""

    max_login_attempts: int = 3
    lockout_minutes: int = 15
    refresh_token_ttl_days: int = 30
    reset_token_ttl_min: int = 30
    verification_token_ttl_hours: int = 24
    invitation_token_ttl_hours: int = 72
    app_base_url: str = "http://app.local"

    tenants: FakeTenantRepository = field(default_factory=FakeTenantRepository)
    users: FakeUserRepository = field(default_factory=FakeUserRepository)
    refresh_tokens: FakeRefreshTokenRepository = field(default_factory=FakeRefreshTokenRepository)
    reset_tokens: FakeResetTokenRepository = field(default_factory=FakeResetTokenRepository)
    verification_tokens: FakeVerificationTokenRepository = field(
        default_factory=FakeVerificationTokenRepository
    )
    invitations: FakeInvitationRepository = field(default_factory=FakeInvitationRepository)
    audit: FakeAuditRepository = field(default_factory=FakeAuditRepository)
    tenant_context: FakeTenantContext = field(default_factory=FakeTenantContext)
    hasher: FakePasswordHasher = field(default_factory=FakePasswordHasher)
    tokens: FakeTokenService = field(default_factory=FakeTokenService)
    email: FakeEmailSender = field(default_factory=FakeEmailSender)

    def authenticate(self) -> Authenticate:
        return Authenticate(
            self.users,
            self.tenants,
            self.hasher,
            self.tokens,
            self.refresh_tokens,
            self.audit,
            self.tenant_context,
            self.max_login_attempts,
            self.lockout_minutes,
            self.refresh_token_ttl_days,
        )

    def refresh(self) -> RefreshAccessToken:
        return RefreshAccessToken(
            self.refresh_tokens,
            self.users,
            self.tokens,
            self.audit,
            self.tenant_context,
            self.refresh_token_ttl_days,
        )

    def logout(self) -> Logout:
        return Logout(self.refresh_tokens, self.tokens, self.audit, self.tenant_context)

    def change_password(self) -> ChangePassword:
        return ChangePassword(
            self.users, self.hasher, self.refresh_tokens, self.audit, self.tenant_context
        )

    def request_password_reset(self) -> RequestPasswordReset:
        return RequestPasswordReset(
            self.tenants,
            self.users,
            self.reset_tokens,
            self.tokens,
            self.email,
            self.tenant_context,
            self.reset_token_ttl_min,
            self.app_base_url,
        )

    def reset_password(self) -> ResetPassword:
        return ResetPassword(
            self.reset_tokens,
            self.users,
            self.hasher,
            self.tokens,
            self.refresh_tokens,
            self.audit,
            self.tenant_context,
        )

    def verify_email(self) -> VerifyEmail:
        return VerifyEmail(
            self.verification_tokens, self.users, self.tokens, self.audit, self.tenant_context
        )

    def onboard_tenant(self) -> OnboardTenant:
        return OnboardTenant(
            self.tenants,
            self.users,
            self.verification_tokens,
            self.hasher,
            self.tokens,
            self.email,
            self.audit,
            self.tenant_context,
            self.verification_token_ttl_hours,
            self.app_base_url,
        )

    def invite_user(self) -> InviteUser:
        return InviteUser(
            self.users,
            self.invitations,
            self.tenants,
            self.tokens,
            self.email,
            self.audit,
            self.tenant_context,
            self.invitation_token_ttl_hours,
            self.app_base_url,
        )

    def accept_invitation(self) -> AcceptInvitation:
        return AcceptInvitation(
            self.invitations, self.users, self.hasher, self.tokens, self.audit, self.tenant_context
        )

    def seed_tenant(self, *, slug: str = "acme", name: str = "Acme") -> Tenant:
        tenant = Tenant(id=str(uuid4()), slug=slug, name=name)
        self.tenants.by_id[tenant.id] = tenant
        return tenant

    def seed_user(
        self,
        tenant: Tenant,
        *,
        email: str = "owner@acme.com",
        password: str = "Sup3rSecret!",
        role: Role = Role.OWNER,
        email_verified: bool = True,
        active: bool = True,
    ) -> User:
        from app.domain.user.value_objects import Email

        user = User(
            id=str(uuid4()),
            tenant_id=tenant.id,
            email=Email(email),
            role=role,
            password_hash=self.hasher.hash(password),
            email_verified=email_verified,
            active=active,
        )
        self.users.by_id[user.id] = user
        return user
