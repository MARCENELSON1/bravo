from __future__ import annotations

import pytest

from app.application.tenant.fiscal import (
    GetTenantFiscalSettings,
    UpdateTenantFiscalAddress,
)
from app.domain.tenant.exceptions import TenantNotFound
from tests.fakes import Harness


async def test_update_and_get_fiscal_address():
    h = Harness()
    tenant = h.seed_tenant(slug="brooklyn", name="Brooklyn")
    await UpdateTenantFiscalAddress(h.tenants).execute(
        tenant_id=tenant.id,
        street="1218 3rd St",
        city="Santa Monica",
        state="CA",
        zip_code="90404",
    )
    got = await GetTenantFiscalSettings(h.tenants).execute(tenant_id=tenant.id)
    assert got.fiscal_street == "1218 3rd St"
    assert got.fiscal_city == "Santa Monica"
    assert got.fiscal_state == "CA"
    assert got.fiscal_zip == "90404"


async def test_blank_fields_clear():
    h = Harness()
    tenant = h.seed_tenant(slug="x", name="X")
    await UpdateTenantFiscalAddress(h.tenants).execute(
        tenant_id=tenant.id, street="  ", city="", state=None, zip_code="90404"
    )
    got = await GetTenantFiscalSettings(h.tenants).execute(tenant_id=tenant.id)
    assert got.fiscal_street is None
    assert got.fiscal_city is None
    assert got.fiscal_state is None
    assert got.fiscal_zip == "90404"


async def test_update_unknown_tenant_raises():
    h = Harness()
    with pytest.raises(TenantNotFound):
        await UpdateTenantFiscalAddress(h.tenants).execute(
            tenant_id="ghost", street="a", city="b", state="c", zip_code="d"
        )
