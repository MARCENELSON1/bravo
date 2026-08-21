from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TipPayout:
    """Liquidación de propina a un mozo (guarda D). Es un **pasivo neutro al
    resultado**: NO es un egreso del local (no baja la ganancia del mes), solo salda
    lo que ya se le debía al mozo. Por eso vive en su propio ledger y no como Payment
    OUTFLOW."""

    id: str
    tenant_id: str
    waiter_id: str
    amount: int  # minor units
    currency: str
    method: str
    created_at: datetime | None = None


class TipPayoutRepository(ABC):
    """Port de escritura del ledger de liquidaciones. Scopeado por ``tenant_id``."""

    @abstractmethod
    async def add(self, payout: TipPayout) -> None: ...
