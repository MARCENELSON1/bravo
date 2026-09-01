from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SelfPaySettings:
    """Per-tenant pay-from-the-table (Carta QR F3) policy the owner controls.

    ``enabled`` gates the whole diner-pays-online flow (OFF by default → the QR
    menu keeps the F1/F2 behaviour: "call waiter"/"request bill", parity). It only
    ever produces an online charge when the tenant also has MercadoPago connected.
    ``tips_enabled`` (ON by default) decides whether the pay screen offers a tip;
    the owner can switch it off from the UI."""

    enabled: bool = False
    tips_enabled: bool = True


class SelfPaySettingsRepository(ABC):
    """Port to read/update the tenant's self-pay settings. Scoped by ``tenant_id``."""

    @abstractmethod
    async def get(self, tenant_id: str) -> SelfPaySettings: ...

    @abstractmethod
    async def update(self, tenant_id: str, settings: SelfPaySettings) -> None: ...
