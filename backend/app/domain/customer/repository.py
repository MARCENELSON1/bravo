from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.customer.entities import Customer


class CustomerRepository(ABC):
    """Port for customer persistence. Every method is scoped by ``tenant_id``
    (defence in depth on top of RLS)."""

    @abstractmethod
    async def get_by_id(self, tenant_id: str, customer_id: str) -> Customer | None: ...

    @abstractmethod
    async def list(self, tenant_id: str, *, search: str | None = None) -> list[Customer]:
        """Customers ordered by name; ``search`` filters by name or phone."""
        ...

    @abstractmethod
    async def add(self, customer: Customer) -> None: ...

    @abstractmethod
    async def save(self, customer: Customer) -> None: ...

    @abstractmethod
    async def delete(self, tenant_id: str, customer_id: str) -> None: ...
