from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.invoice.credentials import TaxCredential


class TaxCredentialRepository(ABC):
    """One AFIP connection per tenant. Tenant-scoped."""

    @abstractmethod
    async def get_by_tenant(self, tenant_id: str) -> TaxCredential | None: ...

    @abstractmethod
    async def upsert(self, credential: TaxCredential) -> None: ...

    @abstractmethod
    async def delete(self, tenant_id: str) -> None: ...
