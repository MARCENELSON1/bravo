from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.table.entities import Table


class TableRepository(ABC):
    """Port for table persistence. Every method is scoped by ``tenant_id``."""

    @abstractmethod
    async def get_by_id(self, tenant_id: str, table_id: str) -> Table | None: ...

    @abstractmethod
    async def list(self, tenant_id: str) -> list[Table]: ...

    @abstractmethod
    async def add(self, table: Table) -> None: ...

    @abstractmethod
    async def save(self, table: Table) -> None: ...
