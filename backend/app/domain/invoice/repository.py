from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.invoice.entities import Invoice


class InvoiceRepository(ABC):
    """Persistence for comprobantes. Every method is scoped by ``tenant_id``."""

    @abstractmethod
    async def get_by_id(self, tenant_id: str, invoice_id: str) -> Invoice | None: ...

    @abstractmethod
    async def get_by_order(self, tenant_id: str, order_id: str) -> Invoice | None: ...

    @abstractmethod
    async def list(self, tenant_id: str) -> list[Invoice]: ...

    @abstractmethod
    async def add(self, invoice: Invoice) -> None: ...

    @abstractmethod
    async def save(self, invoice: Invoice) -> None: ...
