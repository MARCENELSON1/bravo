from abc import ABC, abstractmethod

from app.domain.tenant.entities import Tenant


class TenantRepository(ABC):
    """Port for tenant persistence. The tenants table is NOT tenant-scoped."""

    @abstractmethod
    async def get_by_id(self, tenant_id: str) -> Tenant | None: ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Tenant | None: ...

    @abstractmethod
    async def add(self, tenant: Tenant) -> None: ...

    @abstractmethod
    async def update_fiscal_address(
        self,
        tenant_id: str,
        *,
        street: str | None,
        city: str | None,
        state: str | None,
        zip_code: str | None,
    ) -> None: ...
