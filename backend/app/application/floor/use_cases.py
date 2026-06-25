from __future__ import annotations

from app.application.floor.dtos import FloorTable
from app.domain.identity.ports import TenantContext
from app.domain.order.entities import Order
from app.domain.order.repository import OrderRepository
from app.domain.table.repository import TableRepository


class GetFloor:
    """Read model: every active table with its current active order (if any).

    Crosses two aggregates (tables + orders) read-only — the table's status is
    *derived* (free vs occupied), never stored, so there is nothing to keep in
    sync. Both queries are tenant-scoped (RLS + explicit filter).
    """

    def __init__(
        self,
        tables: TableRepository,
        orders: OrderRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._tables = tables
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> list[FloorTable]:
        self._tenant_context.set(tenant_id)
        tables = await self._tables.list(tenant_id)
        active = await self._orders.list_active(tenant_id)
        # list_active is ordered oldest-first → setdefault keeps the earliest
        # open order per table (the one actually being served).
        by_table: dict[str, Order] = {}
        for order in active:
            by_table.setdefault(order.table_id, order)
        return [
            FloorTable(table=table, order=by_table.get(table.id))
            for table in tables
            if table.active
        ]
