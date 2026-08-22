from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.table_session.entities import TableSession


class TableSessionRepository(ABC):
    """Port for the table-session aggregate. Every method is scoped by
    ``tenant_id`` (defence in depth on top of RLS)."""

    @abstractmethod
    async def get_by_id(self, tenant_id: str, session_id: str) -> TableSession | None: ...

    @abstractmethod
    async def get_open_by_table(
        self, tenant_id: str, table_id: str
    ) -> TableSession | None:
        """The one open (not closed, not merged) session for a table, if any."""
        ...

    @abstractmethod
    async def list_open(self, tenant_id: str) -> list[TableSession]:
        """Every open session (what the floor crosses with the tables)."""
        ...

    @abstractmethod
    async def add(self, session: TableSession) -> None: ...

    @abstractmethod
    async def save(self, session: TableSession) -> None: ...
