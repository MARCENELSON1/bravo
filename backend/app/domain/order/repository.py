from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.order.entities import Order
from app.domain.order.value_objects import OrderStatus


class OrderRepository(ABC):
    """Port for order persistence. Every method is scoped by ``tenant_id``."""

    @abstractmethod
    async def get_by_id(self, tenant_id: str, order_id: str) -> Order | None: ...

    @abstractmethod
    async def list_by_status(
        self, tenant_id: str, status: OrderStatus | None = None
    ) -> list[Order]: ...

    @abstractmethod
    async def list_kds(self, tenant_id: str) -> list[Order]: ...

    @abstractmethod
    async def list_active(self, tenant_id: str) -> list[Order]:
        """Orders that still occupy a table (everything but PAID/CANCELLED)."""

    @abstractmethod
    async def add(self, order: Order) -> None: ...

    @abstractmethod
    async def save(self, order: Order) -> None: ...
