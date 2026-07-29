"""Analytics ports. The payment settle depends on ``SalesProjector`` (a port),
never on the analytics implementation — dependencies point inward."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from app.application.analytics.facts import SaleFact


class SalesProjector(ABC):
    """Project a PAID order into the canonical sale_facts (silver). Must be
    idempotent: calling it twice for the same order writes the facts once."""

    @abstractmethod
    async def project_order(self, tenant_id: str, order_id: str) -> None: ...

    @abstractmethod
    async def reverse_order(self, tenant_id: str, order_id: str) -> None:
        """Inverse of ``project_order``: drop the order's facts (a reopen). Must
        be idempotent so the facts re-project cleanly on a re-pay."""
        ...


class FinanceSnapshotWriter(ABC):
    """Mantiene los totales diarios pre-agregados (Tanda F). Incremental: los
    deltas se suman al día (negativos al revertir). Scopeado por ``tenant_id``."""

    @abstractmethod
    async def add(
        self,
        tenant_id: str,
        day: date,
        *,
        sales_amount: int,
        food_cost_amount: int,
        orders_count: int,
        units_sold: int,
    ) -> None: ...


class FinanceSnapshotRebuilder(ABC):
    """Reconstruye los snapshots diarios desde el historial canónico (sale_facts).
    Scopeado por ``tenant_id``. Devuelve la cantidad de días reconstruidos."""

    @abstractmethod
    async def rebuild(self, tenant_id: str) -> int: ...


class SaleFactsRepository(ABC):
    """Persistence port for the canonical sale_facts. Scoped by ``tenant_id``."""

    @abstractmethod
    async def exists_for_order(self, tenant_id: str, order_id: str) -> bool: ...

    @abstractmethod
    async def add_many(self, facts: list[SaleFact]) -> None: ...

    @abstractmethod
    async def list_for_order(self, tenant_id: str, order_id: str) -> list[SaleFact]: ...

    @abstractmethod
    async def delete_for_order(self, tenant_id: str, order_id: str) -> None: ...
