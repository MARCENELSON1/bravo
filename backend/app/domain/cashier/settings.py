from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class CashSettings:
    """Per-tenant cash policy the owner controls: whether a cobro needs an open
    caja (guarda B3) and whether the arqueo is blind (count without seeing the
    esperado). Both default OFF (parity)."""

    require_open_cash_session: bool = False
    blind_cash_count: bool = False


class CashSettingsRepository(ABC):
    """Port to read/update the tenant's cash settings. Scoped by ``tenant_id``."""

    @abstractmethod
    async def get(self, tenant_id: str) -> CashSettings: ...

    @abstractmethod
    async def update(self, tenant_id: str, settings: CashSettings) -> None: ...
