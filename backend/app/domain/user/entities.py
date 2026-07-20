from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.user.exceptions import EmailNotVerified, InactiveUser, UserLocked
from app.domain.user.value_objects import Email, Role


@dataclass
class User:
    """A user account scoped to a tenant.

    Business rules (lockout, login eligibility) live here; cryptography does not
    — password verification is delegated to the ``PasswordHasher`` port.
    """

    id: str
    tenant_id: str
    email: Email
    role: Role
    name: str | None = None
    hourly_rate_amount: int | None = None  # minor units; None → sin rate cargado
    password_hash: str | None = None
    email_verified: bool = False
    active: bool = True
    failed_attempts: int = 0
    locked_until: datetime | None = None
    created_at: datetime | None = None

    def is_locked(self, now: datetime) -> bool:
        return self.locked_until is not None and self.locked_until > now

    def can_login(self, now: datetime) -> None:
        """Raise the appropriate domain error if this user may not log in."""
        if not self.active:
            raise InactiveUser()
        if self.is_locked(now):
            raise UserLocked()
        if not self.email_verified:
            raise EmailNotVerified()

    def register_failed_attempt(
        self, now: datetime, max_attempts: int, lockout_minutes: int
    ) -> None:
        """Count a failed login; lock the account once the threshold is reached."""
        self.failed_attempts += 1
        if self.failed_attempts >= max_attempts:
            self.locked_until = now + timedelta(minutes=lockout_minutes)
            self.failed_attempts = 0

    def reset_attempts(self) -> None:
        self.failed_attempts = 0
        self.locked_until = None

    def set_password(self, password_hash: str) -> None:
        self.password_hash = password_hash

    def mark_email_verified(self) -> None:
        self.email_verified = True

    def activate(self) -> None:
        self.active = True
