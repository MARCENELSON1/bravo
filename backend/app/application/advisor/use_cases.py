"""Advisor cost-profile settings (read + upsert)."""

from __future__ import annotations

from app.domain.advisor.entities import AdvisorSettings
from app.domain.advisor.repository import AdvisorDiagnosticsCache, AdvisorSettingsRepository
from app.domain.identity.ports import TenantContext
from app.domain.shared.money import Money
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.tenant.repository import TenantRepository


class RebuildAdvisorDiagnostics:
    """Rebuild manual del caché de diagnósticos: purga lo cacheado del tenant;
    el próximo request regenera (narrator/synthesizer). La invalidación normal es
    automática (el fingerprint cambia con la data) — esto es el botón de escape."""

    def __init__(self, cache: AdvisorDiagnosticsCache, tenant_context: TenantContext) -> None:
        self._cache = cache
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> int:
        self._tenant_context.set(tenant_id)
        return await self._cache.purge(tenant_id)


class GetAdvisorSettings:
    def __init__(
        self, settings: AdvisorSettingsRepository, tenant_context: TenantContext
    ) -> None:
        self._settings = settings
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> AdvisorSettings | None:
        self._tenant_context.set(tenant_id)
        return await self._settings.get(tenant_id)


class UpdateAdvisorSettings:
    """Upsert the tenant's cost profile (costs expressed in the tenant currency)."""

    def __init__(
        self,
        settings: AdvisorSettingsRepository,
        tenants: TenantRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._settings = settings
        self._tenants = tenants
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        monthly_labor_cost: int,
        monthly_other_fixed_costs: int,
        target_food_cost_bps: int,
    ) -> AdvisorSettings:
        self._tenant_context.set(tenant_id)
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFound()
        settings = AdvisorSettings(
            tenant_id=tenant_id,
            monthly_labor_cost=Money(monthly_labor_cost, tenant.currency),
            monthly_other_fixed_costs=Money(monthly_other_fixed_costs, tenant.currency),
            target_food_cost_bps=target_food_cost_bps,
        )
        await self._settings.save(settings)
        return settings
