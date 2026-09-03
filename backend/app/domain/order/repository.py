from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.order.entities import Order
from app.domain.order.value_objects import OrderStatus, Station


class OrderRepository(ABC):
    """Port for order persistence. Every method is scoped by ``tenant_id``."""

    @abstractmethod
    async def get_by_id(self, tenant_id: str, order_id: str) -> Order | None: ...

    @abstractmethod
    async def list_by_status(
        self, tenant_id: str, status: OrderStatus | None = None
    ) -> list[Order]: ...

    @abstractmethod
    async def list_kds(
        self, tenant_id: str, station: Station | None = None
    ) -> list[Order]: ...

    @abstractmethod
    async def list_active(self, tenant_id: str) -> list[Order]:
        """Orders that still occupy a table (everything but PAID/CANCELLED)."""

    @abstractmethod
    async def list_open_by_session(
        self, tenant_id: str, session_id: str
    ) -> list[Order]:
        """Open (not PAID/CANCELLED) orders of a floor session — the running bill of
        that table (Carta QR F3). Orders carry ``session_id`` but nothing queried by
        it until now."""

    @abstractmethod
    async def list_pending_qr(self, tenant_id: str) -> list[Order]:
        """QR orders still waiting to be confirmed: ``status=OPEN`` +
        ``source=CUSTOMER_QR`` (the "QR por confirmar" tray, Fase 2)."""

    @abstractmethod
    async def add(self, order: Order) -> None: ...

    @abstractmethod
    async def save(self, order: Order) -> None: ...
