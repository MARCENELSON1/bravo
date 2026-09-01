from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SelfOrderSettings:
    """Per-tenant self-order (Carta QR) policy the owner controls.

    ``enabled`` gates the whole customer-order flow (OFF by default → the QR menu
    is read-only, parity). ``requires_confirmation`` is the kitchen gate: when ON
    (default) a customer order lands PENDING and the waiter confirms (marches) it;
    when OFF it auto-marches straight to the KDS."""

    enabled: bool = False
    requires_confirmation: bool = True


class SelfOrderSettingsRepository(ABC):
    """Port to read/update the tenant's self-order settings. Scoped by ``tenant_id``."""

    @abstractmethod
    async def get(self, tenant_id: str) -> SelfOrderSettings: ...

    @abstractmethod
    async def update(self, tenant_id: str, settings: SelfOrderSettings) -> None: ...
