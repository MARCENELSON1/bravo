from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.user.entities import User
from app.domain.user.exceptions import (
    EmailNotVerified,
    InactiveUser,
    InvalidEmail,
    UserLocked,
)
from app.domain.user.value_objects import Email, Role


def _user(
    *,
    email_verified: bool = True,
    active: bool = True,
    locked_until: datetime | None = None,
    failed_attempts: int = 0,
) -> User:
    return User(
        id="u",
        tenant_id="t",
        email=Email("a@b.com"),
        role=Role.OWNER,
        password_hash="hashed:pw",
        email_verified=email_verified,
        active=active,
        failed_attempts=failed_attempts,
        locked_until=locked_until,
    )


def test_email_invalid_raises():
    with pytest.raises(InvalidEmail):
        Email("not-an-email")


def test_email_normalizes():
    assert Email("  A@B.COM ").value == "a@b.com"


def test_can_login_ok():
    _user().can_login(datetime.now(UTC))  # must not raise


def test_can_login_locked():
    now = datetime.now(UTC)
    with pytest.raises(UserLocked):
        _user(locked_until=now + timedelta(minutes=5)).can_login(now)


def test_can_login_unverified():
    with pytest.raises(EmailNotVerified):
        _user(email_verified=False).can_login(datetime.now(UTC))


def test_can_login_inactive():
    with pytest.raises(InactiveUser):
        _user(active=False).can_login(datetime.now(UTC))


def test_lockout_after_max_attempts():
    now = datetime.now(UTC)
    user = _user()
    user.register_failed_attempt(now, 3, 15)
    user.register_failed_attempt(now, 3, 15)
    assert user.failed_attempts == 2
    assert not user.is_locked(now)
    user.register_failed_attempt(now, 3, 15)
    assert user.is_locked(now)
    assert user.failed_attempts == 0


def test_reset_attempts_clears_lock():
    now = datetime.now(UTC)
    user = _user(failed_attempts=2, locked_until=now + timedelta(minutes=5))
    user.reset_attempts()
    assert user.failed_attempts == 0
    assert user.locked_until is None
    assert not user.is_locked(now)
