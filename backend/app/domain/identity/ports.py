"""Identity ports (interfaces). Implementations live in ``infrastructure``.

These cover external services (password hashing, tokens, email), the tenant
context used to scope Postgres RLS, and the persistence ports for the auth
token tables and the audit log.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.identity.tokens import (
    AccessClaims,
    AuthAuditEntry,
    EmailVerificationToken,
    Invitation,
    PasswordResetToken,
    RefreshToken,
)
from app.domain.user.value_objects import Role


class TenantContext(ABC):
    """Establishes the current tenant for the request (drives Postgres RLS)."""

    @abstractmethod
    def set(self, tenant_id: str) -> None: ...

    @abstractmethod
    def get(self) -> str | None: ...


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str: ...

    @abstractmethod
    def verify(self, password: str, password_hash: str) -> bool: ...


class TokenService(ABC):
    """Access (JWT) tokens and opaque one-time tokens.

    Opaque tokens are formatted ``"{tenant_id}.{secret}"`` so flows that run
    without an access token (refresh, reset, verify, invitation) can derive the
    tenant and establish RLS scope. Only the hash of an opaque token is stored.
    """

    @abstractmethod
    def create_access_token(self, *, user_id: str, tenant_id: str, role: Role) -> str: ...

    @abstractmethod
    def decode_access_token(self, token: str) -> AccessClaims: ...

    @abstractmethod
    def generate_opaque_token(self, tenant_id: str) -> str: ...

    @abstractmethod
    def read_tenant(self, token: str) -> str: ...

    @abstractmethod
    def hash_token(self, token: str) -> str: ...

    @abstractmethod
    def verify_token(self, token: str, token_hash: str) -> bool: ...


class EmailSender(ABC):
    """Sends transactional emails. Copy/templates are in Spanish (UX)."""

    @abstractmethod
    async def send_email_verification(self, *, to: str, link: str) -> None: ...

    @abstractmethod
    async def send_password_reset(self, *, to: str, link: str) -> None: ...

    @abstractmethod
    async def send_invitation(self, *, to: str, link: str, tenant_name: str) -> None: ...


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def add(self, token: RefreshToken) -> None: ...

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...

    @abstractmethod
    async def revoke(self, token_id: str) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, tenant_id: str, user_id: str) -> None: ...


class ResetTokenRepository(ABC):
    @abstractmethod
    async def add(self, token: PasswordResetToken) -> None: ...

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> PasswordResetToken | None: ...

    @abstractmethod
    async def mark_used(self, token_id: str) -> None: ...

    @abstractmethod
    async def invalidate_for_user(self, tenant_id: str, user_id: str) -> None: ...


class VerificationTokenRepository(ABC):
    @abstractmethod
    async def add(self, token: EmailVerificationToken) -> None: ...

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> EmailVerificationToken | None: ...

    @abstractmethod
    async def mark_used(self, token_id: str) -> None: ...


class InvitationRepository(ABC):
    @abstractmethod
    async def add(self, invitation: Invitation) -> None: ...

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> Invitation | None: ...

    @abstractmethod
    async def mark_used(self, invitation_id: str) -> None: ...


class AuditRepository(ABC):
    @abstractmethod
    async def record(self, entry: AuthAuditEntry) -> None: ...
