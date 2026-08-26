from __future__ import annotations

import pytest

from app.domain.identity.tokens import AccessClaims
from app.domain.user.entities import User
from app.domain.user.exceptions import InsufficientRole
from app.domain.user.value_objects import Email, Role
from app.presentation.rbac import require_platform_admin


def _user(*, platform_admin: bool) -> User:
    return User(
        id="u1",
        tenant_id="t1",
        email=Email("admin@wellnod.com"),
        role=Role.OWNER,
        platform_admin=platform_admin,
    )


class _FakeUsers:
    def __init__(self, user: User | None) -> None:
        self._user = user

    async def get_by_id(self, tenant_id: str, user_id: str) -> User | None:
        return self._user


_IDENTITY = AccessClaims(user_id="u1", tenant_id="t1", role=Role.OWNER)


def test_user_defaults_to_not_platform_admin():
    assert _user(platform_admin=False).platform_admin is False


async def test_allows_platform_admin():
    result = await require_platform_admin(
        identity=_IDENTITY, users=_FakeUsers(_user(platform_admin=True))
    )
    assert result is _IDENTITY


async def test_rejects_non_admin():
    with pytest.raises(InsufficientRole):
        await require_platform_admin(
            identity=_IDENTITY, users=_FakeUsers(_user(platform_admin=False))
        )


async def test_rejects_when_user_missing():
    with pytest.raises(InsufficientRole):
        await require_platform_admin(identity=_IDENTITY, users=_FakeUsers(None))
