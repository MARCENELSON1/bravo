from __future__ import annotations

import pytest

from app.application.identity.get_my_profile import GetMyProfile
from app.domain.tenant.entities import Tenant
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.user.entities import User
from app.domain.user.exceptions import UserNotFound
from app.domain.user.value_objects import Email, Role
from tests.fakes import FakeTenantContext, FakeTenantRepository, FakeUserRepository


def _use_case(users: FakeUserRepository, tenants: FakeTenantRepository) -> GetMyProfile:
    return GetMyProfile(users=users, tenants=tenants, tenant_context=FakeTenantContext())


async def test_returns_names_for_user_and_tenant() -> None:
    users, tenants = FakeUserRepository(), FakeTenantRepository()
    await tenants.add(Tenant(id="t1", slug="trattoria", name="La Trattoria"))
    await users.add(
        User(id="u1", tenant_id="t1", email=Email("juan@resto.com"), role=Role.OWNER,
             name="Juan Pérez")
    )

    profile = await _use_case(users, tenants).execute(tenant_id="t1", user_id="u1")

    assert profile.name == "Juan Pérez"
    assert profile.email == "juan@resto.com"
    assert profile.tenant_name == "La Trattoria"
    assert profile.role == "OWNER"


async def test_name_is_optional() -> None:
    users, tenants = FakeUserRepository(), FakeTenantRepository()
    await tenants.add(Tenant(id="t1", slug="bar", name="Bar Uno"))
    await users.add(
        User(id="u1", tenant_id="t1", email=Email("x@bar.com"), role=Role.MANAGER)
    )

    profile = await _use_case(users, tenants).execute(tenant_id="t1", user_id="u1")

    assert profile.name is None  # la UI saluda sin nombre y usa el email para iniciales
    assert profile.tenant_name == "Bar Uno"


async def test_unknown_user_or_tenant_raise() -> None:
    users, tenants = FakeUserRepository(), FakeTenantRepository()
    await tenants.add(Tenant(id="t1", slug="bar", name="Bar Uno"))

    with pytest.raises(UserNotFound):
        await _use_case(users, tenants).execute(tenant_id="t1", user_id="nope")

    await users.add(
        User(id="u1", tenant_id="huerfano", email=Email("x@bar.com"), role=Role.OWNER)
    )
    with pytest.raises(TenantNotFound):
        await _use_case(users, tenants).execute(tenant_id="huerfano", user_id="u1")
