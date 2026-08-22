from __future__ import annotations

from uuid import uuid4

from app.application.table.dtos import CreateTableResult
from app.domain.identity.ports import TenantContext
from app.domain.table.entities import Table
from app.domain.table.exceptions import TableNotFound
from app.domain.table.repository import TableRepository


class CreateTable:
    def __init__(self, tables: TableRepository, tenant_context: TenantContext) -> None:
        self._tables = tables
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, number: int, name: str | None
    ) -> CreateTableResult:
        self._tenant_context.set(tenant_id)
        table = Table(id=str(uuid4()), tenant_id=tenant_id, number=number, name=name)
        await self._tables.add(table)
        return CreateTableResult(table_id=table.id)


class ListTables:
    def __init__(self, tables: TableRepository, tenant_context: TenantContext) -> None:
        self._tables = tables
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> list[Table]:
        self._tenant_context.set(tenant_id)
        return await self._tables.list(tenant_id)


# Sentinel so a PATCH can distinguish "clear this field" (None) from "leave it".
_UNSET = object()


class UpdateTable:
    """Patch a table's floor config: its sector and its capacity (the PAX
    default). Only the fields provided are touched — passing ``None`` clears a
    field, omitting it (``_UNSET``) leaves it as is (parity)."""

    def __init__(self, tables: TableRepository, tenant_context: TenantContext) -> None:
        self._tables = tables
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        table_id: str,
        sector_id: str | None | object = _UNSET,
        capacity: int | None | object = _UNSET,
    ) -> Table:
        self._tenant_context.set(tenant_id)
        table = await self._tables.get_by_id(tenant_id, table_id)
        if table is None:
            raise TableNotFound()
        if sector_id is not _UNSET:
            table.sector_id = sector_id  # type: ignore[assignment]
        if capacity is not _UNSET:
            table.capacity = capacity  # type: ignore[assignment]
        await self._tables.save(table)
        return table
