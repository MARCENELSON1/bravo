from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.identity.exceptions import ExpiredToken, InvalidToken
from app.domain.identity.tokens import RefreshToken
from app.domain.user.exceptions import EmailNotVerified, InvalidCredentials, UserLocked
from tests.fakes import Harness


async def test_login_happy_issues_tokens_and_audits():
    h = Harness()
    tenant = h.seed_tenant(slug="acme")
    user = h.seed_user(tenant, email="owner@acme.com", password="pw")
    tokens = await h.authenticate().execute(
        tenant_slug="acme", email="OWNER@acme.com", password="pw"
    )
    assert tokens.access_token.startswith("access:")
    assert tokens.token_type == "bearer"
    assert len(h.refresh_tokens.items) == 1
    assert "login_success" in h.audit.events()
    assert h.tenant_context.current == tenant.id
    assert h.users.by_id[user.id].failed_attempts == 0


async def test_login_wrong_password_increments_and_is_neutral():
    h = Harness()
    tenant = h.seed_tenant()
    user = h.seed_user(tenant, password="pw")
    with pytest.raises(InvalidCredentials):
        await h.authenticate().execute(
            tenant_slug=tenant.slug, email=str(user.email), password="bad"
        )
    assert h.users.by_id[user.id].failed_attempts == 1
    assert "login_failed" in h.audit.events()


async def test_login_unknown_email_is_neutral():
    h = Harness()
    tenant = h.seed_tenant()
    with pytest.raises(InvalidCredentials):
        await h.authenticate().execute(
            tenant_slug=tenant.slug, email="nobody@acme.com", password="x"
        )


async def test_login_unknown_tenant_is_neutral():
    h = Harness()
    with pytest.raises(InvalidCredentials):
        await h.authenticate().execute(tenant_slug="ghost", email="a@b.com", password="x")


async def test_login_locks_after_max_attempts():
    h = Harness(max_login_attempts=2)
    tenant = h.seed_tenant()
    user = h.seed_user(tenant, password="pw")
    for _ in range(2):
        with pytest.raises(InvalidCredentials):
            await h.authenticate().execute(
                tenant_slug=tenant.slug, email=str(user.email), password="bad"
            )
    with pytest.raises(UserLocked):
        await h.authenticate().execute(
            tenant_slug=tenant.slug, email=str(user.email), password="pw"
        )


async def test_login_unverified_revealed_only_after_correct_password():
    h = Harness()
    tenant = h.seed_tenant()
    user = h.seed_user(tenant, password="pw", email_verified=False)
    with pytest.raises(EmailNotVerified):
        await h.authenticate().execute(
            tenant_slug=tenant.slug, email=str(user.email), password="pw"
        )


async def test_refresh_rotates_and_revokes_old():
    h = Harness()
    tenant = h.seed_tenant()
    user = h.seed_user(tenant, password="pw")
    tokens = await h.authenticate().execute(
        tenant_slug=tenant.slug, email=str(user.email), password="pw"
    )
    new_tokens = await h.refresh().execute(refresh_token=tokens.refresh_token)
    assert new_tokens.refresh_token != tokens.refresh_token
    old = await h.refresh_tokens.get_by_hash(h.tokens.hash_token(tokens.refresh_token))
    assert old is not None and old.revoked
    assert "token_refreshed" in h.audit.events()


async def test_refresh_expired_raises():
    h = Harness()
    tenant = h.seed_tenant()
    user = h.seed_user(tenant)
    raw = h.tokens.generate_opaque_token(tenant.id)
    await h.refresh_tokens.add(
        RefreshToken(
            id=str(uuid4()),
            tenant_id=tenant.id,
            user_id=user.id,
            token_hash=h.tokens.hash_token(raw),
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    )
    with pytest.raises(ExpiredToken):
        await h.refresh().execute(refresh_token=raw)


async def test_refresh_revoked_is_invalid():
    h = Harness()
    tenant = h.seed_tenant()
    user = h.seed_user(tenant)
    raw = h.tokens.generate_opaque_token(tenant.id)
    await h.refresh_tokens.add(
        RefreshToken(
            id="r1",
            tenant_id=tenant.id,
            user_id=user.id,
            token_hash=h.tokens.hash_token(raw),
            expires_at=datetime.now(UTC) + timedelta(days=1),
            revoked=True,
        )
    )
    with pytest.raises(InvalidToken):
        await h.refresh().execute(refresh_token=raw)


async def test_refresh_malformed_token_is_invalid():
    h = Harness()
    with pytest.raises(InvalidToken):
        await h.refresh().execute(refresh_token="no-dot-token")


async def test_logout_revokes_refresh_token():
    h = Harness()
    tenant = h.seed_tenant()
    user = h.seed_user(tenant, password="pw")
    tokens = await h.authenticate().execute(
        tenant_slug=tenant.slug, email=str(user.email), password="pw"
    )
    await h.logout().execute(refresh_token=tokens.refresh_token)
    rec = await h.refresh_tokens.get_by_hash(h.tokens.hash_token(tokens.refresh_token))
    assert rec is not None and rec.revoked
    assert "logout" in h.audit.events()


async def test_logout_with_garbage_token_is_silent():
    h = Harness()
    await h.logout().execute(refresh_token="garbage")  # must not raise


async def test_change_password_happy_revokes_sessions():
    h = Harness()
    tenant = h.seed_tenant()
    user = h.seed_user(tenant, password="old")
    tokens = await h.authenticate().execute(
        tenant_slug=tenant.slug, email=str(user.email), password="old"
    )
    await h.change_password().execute(
        tenant_id=tenant.id, user_id=user.id, current_password="old", new_password="new"
    )
    assert h.users.by_id[user.id].password_hash == h.hasher.hash("new")
    rec = await h.refresh_tokens.get_by_hash(h.tokens.hash_token(tokens.refresh_token))
    assert rec is not None and rec.revoked
    assert "password_changed" in h.audit.events()


async def test_change_password_wrong_current_raises():
    h = Harness()
    tenant = h.seed_tenant()
    user = h.seed_user(tenant, password="old")
    with pytest.raises(InvalidCredentials):
        await h.change_password().execute(
            tenant_id=tenant.id, user_id=user.id, current_password="bad", new_password="new"
        )
