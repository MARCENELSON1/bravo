from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.advisor.entities import AdvisorSettings


class AdvisorSettingsRepository(ABC):
    """Port for the per-tenant cost profile (1:1). Scoped by ``tenant_id``."""

    @abstractmethod
    async def get(self, tenant_id: str) -> AdvisorSettings | None: ...

    @abstractmethod
    async def save(self, settings: AdvisorSettings) -> None: ...
