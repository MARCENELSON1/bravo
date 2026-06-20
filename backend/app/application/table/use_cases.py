from __future__ import annotations

from uuid import uuid4

from app.application.table.dtos import CreateTableResult
from app.domain.identity.ports import TenantContext
from app.domain.table.entities import Table
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
