from __future__ import annotations

from app.application.floor.dtos import FloorSession, FloorTable
from app.domain.identity.ports import TenantContext
from app.domain.order.entities import Order
from app.domain.order.repository import OrderRepository
from app.domain.table.repository import TableRepository
from app.domain.table_session.entities import TableSession
from app.domain.table_session.repository import TableSessionRepository
from app.domain.table_session.status import derive_session_state
from app.domain.user.repository import UserRepository


class GetFloor:
    """Read model: every active table with its current active order (if any)
    and its session-aware live view (derived state + timers + pax).

    Crosses three aggregates (tables + orders + sessions) read-only — the
    table's occupancy and the session's status are *derived*, never stored, so
    there is nothing to keep in sync. Every query is tenant-scoped (RLS +
    explicit filter). Parity: a table with no open session falls back to the
    plain free/occupied view (``session`` is None).
    """

    def __init__(
        self,
        tables: TableRepository,
        orders: OrderRepository,
        sessions: TableSessionRepository,
        users: UserRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._tables = tables
        self._orders = orders
        self._sessions = sessions
        self._users = users
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> list[FloorTable]:
        self._tenant_context.set(tenant_id)
        tables = await self._tables.list(tenant_id)
        active = await self._orders.list_active(tenant_id)
        open_sessions = await self._sessions.list_open(tenant_id)

        # Oldest active order per table (the one actually being served) — parity
        # with the previous binary occupancy read.
        by_table: dict[str, Order] = {}
        orders_by_table: dict[str, list[Order]] = {}
        for order in active:
            by_table.setdefault(order.table_id, order)
            orders_by_table.setdefault(order.table_id, []).append(order)

        # One open session per table (opened_at asc → keep the earliest).
        session_by_table: dict[str, TableSession] = {}
        for s in open_sessions:
            session_by_table.setdefault(s.table_id, s)

        waiter_ids = {s.waiter_id for s in open_sessions if s.waiter_id is not None}
        names = await self._users.names_by_ids(tenant_id, waiter_ids)

        rows: list[FloorTable] = []
        for table in tables:
            if not table.active:
                continue
            order = by_table.get(table.id)
            session = session_by_table.get(table.id)
            floor_session: FloorSession | None = None
            if session is not None:
                derived = derive_session_state(
                    session, orders_by_table.get(table.id, [])
                )
                floor_session = FloorSession(
                    id=session.id,
                    status=derived.status,
                    state_since=derived.since,
                    pax=session.pax,
                    waiter_id=session.waiter_id,
                    waiter_name=(
                        names.get(session.waiter_id) if session.waiter_id else None
                    ),
                    sector_id=table.sector_id,
                )
            rows.append(FloorTable(table=table, order=order, session=floor_session))
        return rows
