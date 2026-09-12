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
    async def list_ids(self) -> list[str]:
        """Every tenant id. Background work (draining the outbox) runs outside any
        request, and row-level security hides tenant-scoped rows until a tenant is
        in context — so a worker starts here and then scopes itself per tenant."""

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

    @abstractmethod
    async def delete(self, tenant_id: str) -> None:
        """Borra el local y TODO lo suyo. Las 44 claves foráneas a ``tenants``
        tienen ``ON DELETE CASCADE``, así que una sola sentencia se lleva
        comandas, cobros, insumos, comprobantes y usuarios. Irreversible."""
