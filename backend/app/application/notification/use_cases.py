from __future__ import annotations

from uuid import uuid4

from app.domain.identity.ports import TenantContext
from app.domain.notification.entities import DeviceToken
from app.domain.notification.repository import DeviceTokenRepository


class RegisterDeviceToken:
    """Register (upsert) the caller's device push token so the mozo can get avisos
    with the app closed. Idempotent by token — the app can re-register on every
    launch/refresh without duplicating."""

    def __init__(
        self, devices: DeviceTokenRepository, tenant_context: TenantContext
    ) -> None:
        self._devices = devices
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, user_id: str, token: str, platform: str
    ) -> None:
        self._tenant_context.set(tenant_id)
        await self._devices.register(
            DeviceToken(
                id=str(uuid4()),
                tenant_id=tenant_id,
                user_id=user_id,
                token=token,
                platform=platform,
            )
        )
