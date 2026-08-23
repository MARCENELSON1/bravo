from __future__ import annotations

from app.domain.tenant.entities import Tenant
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.tenant.repository import TenantRepository


def _clean(value: str | None) -> str | None:
    """Trim; empty → None so a blank field clears (not stores '')."""
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


class GetTenantFiscalSettings:
    """Read the tenant's fiscal/regional settings (regime, engine, address)."""

    def __init__(self, tenants: TenantRepository) -> None:
        self._tenants = tenants

    async def execute(self, *, tenant_id: str) -> Tenant:
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFound()
        return tenant


class UpdateTenantFiscalAddress:
    """Set the tenant's point-of-sale address (needed by a rate-by-address engine
    like TaxJar). Empty fields clear. Regime/engine are derived at onboarding and
    not changed here."""

    def __init__(self, tenants: TenantRepository) -> None:
        self._tenants = tenants

    async def execute(
        self,
        *,
        tenant_id: str,
        street: str | None,
        city: str | None,
        state: str | None,
        zip_code: str | None,
    ) -> Tenant:
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFound()
        street, city, state, zip_code = (
            _clean(street),
            _clean(city),
            _clean(state),
            _clean(zip_code),
        )
        await self._tenants.update_fiscal_address(
            tenant_id, street=street, city=city, state=state, zip_code=zip_code
        )
        tenant.fiscal_street = street
        tenant.fiscal_city = city
        tenant.fiscal_state = state
        tenant.fiscal_zip = zip_code
        return tenant
