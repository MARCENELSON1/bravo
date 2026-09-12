from __future__ import annotations

from app.domain.identity.ports import TenantContext
from app.domain.payment.self_pay_settings import (
    SelfPaySettings,
    SelfPaySettingsRepository,
)


class GetSelfPaySettings:
    def __init__(
        self, settings: SelfPaySettingsRepository, tenant_context: TenantContext
    ) -> None:
        self._settings = settings
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> SelfPaySettings:
        self._tenant_context.set(tenant_id)
        return await self._settings.get(tenant_id)


class UpdateSelfPaySettings:
    """Owner sets the pay-from-the-table policy: enable diner online pay + whether
    the pay screen offers a tip."""

    def __init__(
        self, settings: SelfPaySettingsRepository, tenant_context: TenantContext
    ) -> None:
        self._settings = settings
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, enabled: bool, tips_enabled: bool
    ) -> SelfPaySettings:
        self._tenant_context.set(tenant_id)
        settings = SelfPaySettings(enabled=enabled, tips_enabled=tips_enabled)
        await self._settings.update(tenant_id, settings)
        return settings
