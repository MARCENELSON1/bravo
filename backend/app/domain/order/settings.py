from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class SelfOrderMode(StrEnum):
    """The QR mode the owner picks (Fase 3). A friendly name over the raw flags:

    - ``READ_ONLY``: the QR menu is view-only, no ordering (``enabled=False``).
    - ``SALON``: the diner orders, a waiter confirms (marches) it, pay at the end
      (``enabled`` + ``requires_confirmation``).
    - ``SELF_SERVICE``: the diner pays first; the order is held off the kitchen
      until the payment confirms, then it auto-marches + auto-assigns a waiter
      (``enabled`` + ``prepay_required``)."""

    READ_ONLY = "READ_ONLY"
    SALON = "SALON"
    SELF_SERVICE = "SELF_SERVICE"


@dataclass(frozen=True)
class SelfOrderSettings:
    """Per-tenant self-order (Carta QR) policy the owner controls.

    ``enabled`` gates the whole customer-order flow (OFF by default → the QR menu
    is read-only, parity). ``requires_confirmation`` is the kitchen gate: when ON
    (default) a customer order lands PENDING and the waiter confirms (marches) it;
    when OFF it auto-marches straight to the KDS. ``prepay_required`` (Fase 3) holds
    the order off the kitchen until it's paid (Self-service). The owner-facing
    concept is ``mode``, derived from these flags (storage stays flags → parity)."""

    enabled: bool = False
    requires_confirmation: bool = True
    prepay_required: bool = False

    @property
    def mode(self) -> SelfOrderMode:
        if not self.enabled:
            return SelfOrderMode.READ_ONLY
        if self.prepay_required:
            return SelfOrderMode.SELF_SERVICE
        return SelfOrderMode.SALON

    @staticmethod
    def from_mode(mode: SelfOrderMode) -> SelfOrderSettings:
        """Derive the raw flags from the owner-picked mode."""
        if mode is SelfOrderMode.READ_ONLY:
            return SelfOrderSettings(enabled=False)
        if mode is SelfOrderMode.SELF_SERVICE:
            return SelfOrderSettings(
                enabled=True, requires_confirmation=False, prepay_required=True
            )
        return SelfOrderSettings(enabled=True, requires_confirmation=True)


class SelfOrderSettingsRepository(ABC):
    """Port to read/update the tenant's self-order settings. Scoped by ``tenant_id``."""

    @abstractmethod
    async def get(self, tenant_id: str) -> SelfOrderSettings: ...

    @abstractmethod
    async def update(self, tenant_id: str, settings: SelfOrderSettings) -> None: ...
