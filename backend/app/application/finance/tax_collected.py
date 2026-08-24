from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from app.domain.identity.ports import TenantContext


@dataclass(frozen=True)
class TaxCollected:
    amount: int  # minor units
    currency: str


class TaxCollectedReadModel(ABC):
    @abstractmethod
    async def total(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> TaxCollected: ...


class GetTaxCollected:
    """Σ del sales tax cobrado (CONFIRMED/INFLOW) en la ventana — lo que el local
    le debe al fisco. 0 en AR (los pagos no llevan tax) → read-only, paridad."""

    def __init__(self, read_model: TaxCollectedReadModel, tenant_context: TenantContext) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> TaxCollected:
        self._tenant_context.set(tenant_id)
        return await self._read_model.total(tenant_id, since=since, until=until)
