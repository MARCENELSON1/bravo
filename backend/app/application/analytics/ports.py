"""Analytics ports. The payment settle depends on ``SalesProjector`` (a port),
never on the analytics implementation — dependencies point inward."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.analytics.facts import SaleFact


class SalesProjector(ABC):
    """Project a PAID order into the canonical sale_facts (silver). Must be
    idempotent: calling it twice for the same order writes the facts once."""

    @abstractmethod
    async def project_order(self, tenant_id: str, order_id: str) -> None: ...


class SaleFactsRepository(ABC):
    """Persistence port for the canonical sale_facts. Scoped by ``tenant_id``."""

    @abstractmethod
    async def exists_for_order(self, tenant_id: str, order_id: str) -> bool: ...

    @abstractmethod
    async def add_many(self, facts: list[SaleFact]) -> None: ...

    @abstractmethod
    async def list_for_order(self, tenant_id: str, order_id: str) -> list[SaleFact]: ...
