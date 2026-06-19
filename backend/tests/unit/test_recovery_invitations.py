from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.application.identity.dtos import InviteUserInput, OnboardTenantInput
from app.domain.identity.exceptions import (
    ExpiredToken,
    InvalidInvitation,
    InvalidToken,
    TokenAlreadyUsed,
)
from app.domain.identity.tokens import (
    EmailVerificationToken,
    Invitation,
    PasswordResetToken,
)
from app.domain.tenant.exceptions import TenantAlreadyExists
from app.domain.user.entities import User
from app.domain.user.exceptions import (
    EmailAlreadyRegistered,
    InsufficientRole,
    InvalidEmail,
)
from app.domain.user.value_objects import Email, Role
from tests.fakes import Harness


async def _add_reset_token(h, tenant, user, *, delta=timedelta(minutes=30), used=False):
    raw = h.tokens.generate_opaque_token(tenant.id)
    await h.reset_tokens.add(
        PasswordResetToken(
            id=str(uuid4()),
            tenant_id=tenant.id,
            user_id=user.id,
            token_hash=h.tokens.hash_token(raw),
            expires_at=datetime.now(UTC) + delta,
            used=used,
        )
    )
    return raw


async def test_request_reset_neutral_unknown_tenant():
    h = Harness()
    await h.request_password_reset().execute(tenant_slug="ghost", email="a@b.com")
    assert h.email.sent == []
    assert h.reset_tokens.items == {}


async def test_request_reset_neutral_unknown_email():
    h = Harness()
    tenant = h.seed_tenant()
    await h.request_password_reset().execute(tenant_slug=tenant.slug, email="nobody@x.com")
    assert h.email.sent == []


async def test_request_reset_happy_sends_email_with_link():
    h = Harness()
    tenant = h.seed_tenant()
    user = h.seed_user(tenant)
    await h.request_password_reset().execute(tenant_slug=tenant.slug, email=str(user.email))
    assert len(h.reset_tokens.items) == 1
    assert h.email.last().kind == "reset"
    assert "/reset-password?token=" in h.email.last().link


async def test_reset_password_happy():
    h = Harness()
    tenant = h.seed_tenant()
    user = h.seed_user(tenant, password="old")
    raw = await _add_reset_token(h, tenant, user)
    await h.reset_password().execute(token=raw, new_password="new")
    assert h.users.by_id[user.id].password_hash == h.hasher.hash("new")
    rec = await h.reset_tokens.get_by_hash(h.tokens.hash_token(raw))
    assert rec is not None and rec.used
    assert "password_reset" in h.audit.events()


async def test_reset_password_expired():
    h = Harness()
    tenant = h.seed_tenant()
    user = h.seed_user(tenant)
    raw = await _add_reset_token(h, tenant, user, delta=timedelta(seconds=-1))
    with pytest.raises(ExpiredToken):
        await h.reset_password().execute(token=raw, new_password="new")


async def test_reset_password_already_used():
    h = Harness()
    tenant = h.seed_tenant()
    user = h.seed_user(tenant)
    raw = await _add_reset_token(h, tenant, user, used=True)
    with pytest.raises(TokenAlreadyUsed):
        await h.reset_password().execute(token=raw, new_password="new")


async def test_reset_password_unknown_token():
    h = Harness()
    with pytest.raises(InvalidToken):
        await h.reset_password().execute(token="tenant.unknown", new_password="x")


async def test_verify_email_happy():
    h = Harness()
    tenant = h.seed_tenant()
    user = h.seed_user(tenant, email_verified=False)
    raw = h.tokens.generate_opaque_token(tenant.id)
    await h.verification_tokens.add(
        EmailVerificationToken(
            id=str(uuid4()),
            tenant_id=tenant.id,
            user_id=user.id,
            token_hash=h.tokens.hash_token(raw),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    await h.verify_email().execute(token=raw)
    assert h.users.by_id[user.id].email_verified is True
    rec = await h.verification_tokens.get_by_hash(h.tokens.hash_token(raw))
    assert rec is not None and rec.used


async def test_verify_email_expired():
    h = Harness()
    tenant = h.seed_tenant()
    user = h.seed_user(tenant, email_verified=False)
    raw = h.tokens.generate_opaque_token(tenant.id)
    await h.verification_tokens.add(
        EmailVerificationToken(
            id=str(uuid4()),
            tenant_id=tenant.id,
            user_id=user.id,
            token_hash=h.tokens.hash_token(raw),
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    )
    with pytest.raises(ExpiredToken):
        await h.verify_email().execute(token=raw)


async def test_onboard_creates_owner_and_sends_verification():
    h = Harness()
    result = await h.onboard_tenant().execute(
        OnboardTenantInput(
            tenant_name="Resto",
            tenant_slug="Resto-1",
            owner_email="O@Resto.com",
            owner_password="pw",
        )
    )
    tenant = await h.tenants.get_by_slug("resto-1")
    assert tenant is not None and tenant.id == result.tenant_id
    owner = h.users.by_id[result.user_id]
    assert owner.role is Role.OWNER
    assert owner.email_verified is False
    assert str(owner.email) == "o@resto.com"
    assert h.email.last().kind == "verification"
    assert "tenant_onboarded" in h.audit.events()


async def test_onboard_duplicate_slug():
    h = Harness()
    h.seed_tenant(slug="dup")
    with pytest.raises(TenantAlreadyExists):
        await h.onboard_tenant().execute(
            OnboardTenantInput("X", "dup", "a@b.com", "pw")
        )


async def test_onboard_invalid_email():
    h = Harness()
    with pytest.raises(InvalidEmail):
        await h.onboard_tenant().execute(
            OnboardTenantInput("X", "newslug", "not-an-email", "pw")
        )


async def test_invite_creates_inactive_user_and_sends_email():
    h = Harness()
    tenant = h.seed_tenant()
    owner = h.seed_user(tenant)
    await h.invite_user().execute(
        tenant_id=tenant.id,
        invited_by=owner.id,
        inviter_role=Role.OWNER,
        data=InviteUserInput(email="waiter@acme.com", role=Role.WAITER),
    )
    invited = await h.users.get_by_email(tenant.id, "waiter@acme.com")
    assert invited is not None
    assert invited.active is False
    assert invited.password_hash is None
    assert invited.role is Role.WAITER
    assert len(h.invitations.items) == 1
    assert h.email.last().kind == "invitation"
    assert h.email.last().extra["tenant_name"] == tenant.name


async def test_invite_duplicate_email():
    h = Harness()
    tenant = h.seed_tenant()
    owner = h.seed_user(tenant, email="owner@acme.com")
    with pytest.raises(EmailAlreadyRegistered):
        await h.invite_user().execute(
            tenant_id=tenant.id,
            invited_by=owner.id,
            inviter_role=Role.OWNER,
            data=InviteUserInput(email="owner@acme.com", role=Role.WAITER),
        )


async def test_accept_invitation_happy_activates_and_verifies():
    h = Harness()
    tenant = h.seed_tenant()
    owner = h.seed_user(tenant)
    await h.invite_user().execute(
        tenant_id=tenant.id,
        invited_by=owner.id,
        inviter_role=Role.OWNER,
        data=InviteUserInput(email="waiter@acme.com", role=Role.WAITER),
    )
    token = h.email.last().link.split("token=")[1]
    await h.accept_invitation().execute(token=token, password="newpw")
    invited = await h.users.get_by_email(tenant.id, "waiter@acme.com")
    assert invited is not None
    assert invited.active is True
    assert invited.email_verified is True
    assert invited.password_hash == h.hasher.hash("newpw")
    invitation = next(iter(h.invitations.items.values()))
    assert invitation.used is True
    assert "invitation_accepted" in h.audit.events()


async def test_accept_invitation_invalid_token():
    h = Harness()
    with pytest.raises(InvalidInvitation):
        await h.accept_invitation().execute(token="tenant.bad", password="x")


async def test_accept_invitation_expired():
    h = Harness()
    tenant = h.seed_tenant()
    invited = User(
        id=str(uuid4()),
        tenant_id=tenant.id,
        email=Email("w@acme.com"),
        role=Role.WAITER,
        active=False,
    )
    h.users.by_id[invited.id] = invited
    raw = h.tokens.generate_opaque_token(tenant.id)
    await h.invitations.add(
        Invitation(
            id=str(uuid4()),
            tenant_id=tenant.id,
            user_id=invited.id,
            email="w@acme.com",
            role=Role.WAITER,
            token_hash=h.tokens.hash_token(raw),
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    )
    with pytest.raises(InvalidInvitation):
        await h.accept_invitation().execute(token=raw, password="x")


async def test_invite_respects_role_ceiling():
    h = Harness()
    tenant = h.seed_tenant()
    owner = h.seed_user(tenant)
    # A MANAGER cannot invite a peer MANAGER.
    with pytest.raises(InsufficientRole):
        await h.invite_user().execute(
            tenant_id=tenant.id,
            invited_by=owner.id,
            inviter_role=Role.MANAGER,
            data=InviteUserInput(email="peer@acme.com", role=Role.MANAGER),
        )
    # An OWNER can invite a MANAGER.
    await h.invite_user().execute(
        tenant_id=tenant.id,
        invited_by=owner.id,
        inviter_role=Role.OWNER,
        data=InviteUserInput(email="manager@acme.com", role=Role.MANAGER),
    )
    assert await h.users.get_by_email(tenant.id, "manager@acme.com") is not None


async def test_request_reset_invalidates_previous_tokens():
    h = Harness()
    tenant = h.seed_tenant()
    user = h.seed_user(tenant)
    await h.request_password_reset().execute(tenant_slug=tenant.slug, email=str(user.email))
    await h.request_password_reset().execute(tenant_slug=tenant.slug, email=str(user.email))
    active = [token for token in h.reset_tokens.items.values() if not token.used]
    assert len(active) == 1  # only the newest reset token stays valid
