from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.tax.credentials import TaxJarCredential


class TaxJarCredentialRepository(ABC):
    """Una conexión de TaxJar por tenant. Tenant-scoped."""

    @abstractmethod
    async def get_by_tenant(self, tenant_id: str) -> TaxJarCredential | None: ...

    @abstractmethod
    async def upsert(self, credential: TaxJarCredential) -> None: ...

    @abstractmethod
    async def delete(self, tenant_id: str) -> None: ...
