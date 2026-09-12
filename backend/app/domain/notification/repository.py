from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.notification.entities import DeviceToken


class DeviceTokenRepository(ABC):
    """Port for device-token persistence. Scoped by ``tenant_id``."""

    @abstractmethod
    async def register(self, token: DeviceToken) -> None:
        """Upsert by ``token``: a device that re-registers updates its owner/platform
        instead of duplicating (the same phone can move between users/tenants)."""

    @abstractmethod
    async def list_for_user(
        self, tenant_id: str, user_id: str
    ) -> list[DeviceToken]: ...

    @abstractmethod
    async def delete(self, tenant_id: str, token: str) -> None:
        """Drop a dead token (the gateway reported it UNREGISTERED)."""
