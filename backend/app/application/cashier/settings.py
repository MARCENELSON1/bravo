from __future__ import annotations

from app.domain.cashier.settings import CashSettings, CashSettingsRepository
from app.domain.identity.ports import TenantContext


class GetCashSettings:
    def __init__(
        self, settings: CashSettingsRepository, tenant_context: TenantContext
    ) -> None:
        self._settings = settings
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> CashSettings:
        self._tenant_context.set(tenant_id)
        return await self._settings.get(tenant_id)


class UpdateCashSettings:
    """Set the tenant's cash policy (require open caja + blind arqueo)."""

    def __init__(
        self, settings: CashSettingsRepository, tenant_context: TenantContext
    ) -> None:
        self._settings = settings
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        require_open_cash_session: bool,
        blind_cash_count: bool,
    ) -> CashSettings:
        self._tenant_context.set(tenant_id)
        settings = CashSettings(
            require_open_cash_session=require_open_cash_session,
            blind_cash_count=blind_cash_count,
        )
        await self._settings.update(tenant_id, settings)
        return settings
