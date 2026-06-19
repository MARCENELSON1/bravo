from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from app.application.clock import utcnow
from app.application.identity.dtos import AuthTokens
from app.domain.identity.ports import (
    AuditRepository,
    PasswordHasher,
    RefreshTokenRepository,
    TenantContext,
    TokenService,
)
from app.domain.identity.tokens import AuthAuditEntry, AuthEvent, RefreshToken
from app.domain.tenant.repository import TenantRepository
from app.domain.user.exceptions import InvalidCredentials, UserLocked
from app.domain.user.repository import UserRepository


class Authenticate:
    """Log a user in: validate credentials, enforce lockout, issue tokens.

    All credential failures raise the same ``InvalidCredentials`` (anti-enumeration);
    a missing workspace is treated the same way.
    """

    def __init__(
        self,
        users: UserRepository,
        tenants: TenantRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
        refresh_tokens: RefreshTokenRepository,
        audit: AuditRepository,
        tenant_context: TenantContext,
        max_login_attempts: int,
        lockout_minutes: int,
        refresh_token_ttl_days: int,
    ) -> None:
        self._users = users
        self._tenants = tenants
        self._hasher = hasher
        self._tokens = tokens
        self._refresh_tokens = refresh_tokens
        self._audit = audit
        self._tenant_context = tenant_context
        self._max_login_attempts = max_login_attempts
        self._lockout_minutes = lockout_minutes
        self._refresh_token_ttl_days = refresh_token_ttl_days

    async def execute(self, *, tenant_slug: str, email: str, password: str) -> AuthTokens:
        tenant = await self._tenants.get_by_slug(tenant_slug.strip().lower())
        if tenant is None:
            raise InvalidCredentials()
        self._tenant_context.set(tenant.id)
        now = utcnow()
        user = await self._users.get_by_email(tenant.id, email.strip().lower())
        if user is None:
            await self._record(tenant.id, None, AuthEvent.LOGIN_FAILED, "unknown_email")
            raise InvalidCredentials()
        if user.is_locked(now):
            await self._record(tenant.id, user.id, AuthEvent.LOGIN_LOCKED, None)
            raise UserLocked()
        if not user.password_hash or not self._hasher.verify(password, user.password_hash):
            user.register_failed_attempt(now, self._max_login_attempts, self._lockout_minutes)
            await self._users.save(user)
            await self._record(tenant.id, user.id, AuthEvent.LOGIN_FAILED, "bad_password")
            raise InvalidCredentials()
        # Credentials are valid — only now surface account-state problems.
        user.can_login(now)
        user.reset_attempts()
        await self._users.save(user)
        access = self._tokens.create_access_token(
            user_id=user.id, tenant_id=user.tenant_id, role=user.role
        )
        raw_refresh = self._tokens.generate_opaque_token(user.tenant_id)
        await self._refresh_tokens.add(
            RefreshToken(
                id=str(uuid4()),
                tenant_id=user.tenant_id,
                user_id=user.id,
                token_hash=self._tokens.hash_token(raw_refresh),
                expires_at=now + timedelta(days=self._refresh_token_ttl_days),
            )
        )
        await self._record(tenant.id, user.id, AuthEvent.LOGIN_SUCCESS, None)
        return AuthTokens(access_token=access, refresh_token=raw_refresh)

    async def _record(
        self, tenant_id: str, user_id: str | None, event: AuthEvent, detail: str | None
    ) -> None:
        await self._audit.record(
            AuthAuditEntry(
                id=str(uuid4()),
                tenant_id=tenant_id,
                event=event,
                user_id=user_id,
                detail=detail,
            )
        )
