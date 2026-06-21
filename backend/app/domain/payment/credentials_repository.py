from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.payment.credentials import PaymentCredential


class PaymentCredentialRepository(ABC):
    """Persistence for tenants' payment-provider connections.

    ``get_by_account_id`` is the one cross-tenant lookup (the webhook has no
    tenant yet — it resolves the tenant from the provider's seller id); every
    other method is tenant-scoped.
    """

    @abstractmethod
    async def get_by_tenant(self, tenant_id: str, provider: str) -> PaymentCredential | None: ...

    @abstractmethod
    async def get_by_account_id(self, external_account_id: str) -> PaymentCredential | None: ...

    @abstractmethod
    async def upsert(self, credential: PaymentCredential) -> None: ...

    @abstractmethod
    async def delete(self, tenant_id: str, provider: str) -> None: ...
