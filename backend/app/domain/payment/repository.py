from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.payment.entities import Payment


class PaymentRepository(ABC):
    """Port for payment persistence. Every method is scoped by ``tenant_id``."""

    @abstractmethod
    async def get_by_id(self, tenant_id: str, payment_id: str) -> Payment | None: ...

    @abstractmethod
    async def confirmed_inflows_by_method(
        self, tenant_id: str, since: datetime, until: datetime
    ) -> dict[str, int]:
        """Sum of CONFIRMED inflow payments grouped by method in ``[since, until)``
        (minor units). Feeds the arqueo Z 'esperado por medio'."""

    @abstractmethod
    async def get_by_external_ref(self, tenant_id: str, external_ref: str) -> Payment | None: ...

    @abstractmethod
    async def list_by_order(self, tenant_id: str, order_id: str) -> list[Payment]: ...

    @abstractmethod
    async def list_expenses(self, tenant_id: str) -> list[Payment]: ...

    @abstractmethod
    async def add(self, payment: Payment) -> None: ...

    @abstractmethod
    async def save(self, payment: Payment) -> None: ...
