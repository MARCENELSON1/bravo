from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.application.clock import utcnow
from app.domain.identity.ports import TenantContext
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import CUSTOMER_WAITER_ID
from app.domain.table.exceptions import TableNotFound
from app.domain.table.repository import TableRepository
from app.domain.table_session.entities import TableSession
from app.domain.table_session.exceptions import (
    SessionHasActiveOrders,
    SessionNotFound,
    TableAlreadyAssigned,
)
from app.domain.table_session.repository import TableSessionRepository
from app.domain.table_session.value_objects import SessionStatus


class OpenSession:
    """Open (or reuse) the table's session, stamping who's sitting there.

    Idempotent per table: if a session is already open it's returned untouched
    (the waiter tapping twice, or a race with ``CreateOrder``'s implicit open,
    must never create a second visit). ``pax`` defaults to the table's capacity."""

    def __init__(
        self,
        sessions: TableSessionRepository,
        tables: TableRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._sessions = sessions
        self._tables = tables
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        table_id: str,
        pax: int | None = None,
        waiter_id: str | None = None,
    ) -> TableSession:
        self._tenant_context.set(tenant_id)
        table = await self._tables.get_by_id(tenant_id, table_id)
        if table is None:
            raise TableNotFound()
        existing = await self._sessions.get_open_by_table(tenant_id, table_id)
        if existing is not None:
            return existing
        session = TableSession(
            id=str(uuid4()),
            tenant_id=tenant_id,
            table_id=table_id,
            status=SessionStatus.OPEN,
            pax=pax if pax is not None else table.capacity,
            waiter_id=waiter_id,
            opened_at=utcnow(),
        )
        await self._sessions.add(session)
        return session


class SetSessionPax:
    """Correct how many people are seated (drives RevPASH / cover counts)."""

    def __init__(
        self,
        sessions: TableSessionRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._sessions = sessions
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, session_id: str, pax: int
    ) -> TableSession:
        self._tenant_context.set(tenant_id)
        session = await self._sessions.get_by_id(tenant_id, session_id)
        if session is None:
            raise SessionNotFound()
        session.pax = pax
        await self._sessions.save(session)
        return session


class RequestBill:
    """Flag that the table asked for the bill (→ ``a_cobrar`` on the floor).

    Idempotent: the first request wins, so the timer counts from when they first
    asked, not from the last tap."""

    def __init__(
        self,
        sessions: TableSessionRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._sessions = sessions
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, session_id: str) -> TableSession:
        self._tenant_context.set(tenant_id)
        session = await self._sessions.get_by_id(tenant_id, session_id)
        if session is None:
            raise SessionNotFound()
        if session.bill_requested_at is None:
            session.bill_requested_at = utcnow()
            await self._sessions.save(session)
        return session


class AssignTableWaiter:
    """The single use case that sets/updates the owner of a table's visit.

    Used by: confirming a QR order (the waiter who marches it becomes the owner),
    a waiter *claiming* an orphan table, and a manager *reassigning* the waiter.
    It also stamps the session's live orders with the new owner, so the Fase 1
    ``order.ready`` alert (which reads ``order.waiter_id``) reaches the right waiter.

    ``only_if_unassigned`` guards the *claim* path: a plain waiter can only take a
    table that has no real owner yet (``waiter_id`` None or the QR nil sentinel);
    a manager reassign passes it as False to override an existing owner."""

    def __init__(
        self,
        sessions: TableSessionRepository,
        orders: OrderRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._sessions = sessions
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        session_id: str,
        waiter_id: str,
        only_if_unassigned: bool = False,
        conflict_raises: bool = True,
    ) -> TableSession:
        self._tenant_context.set(tenant_id)
        session = await self._sessions.get_by_id(tenant_id, session_id)
        if session is None:
            raise SessionNotFound()
        is_orphan = session.waiter_id in (None, CUSTOMER_WAITER_ID)
        already_mine = session.waiter_id == waiter_id
        if only_if_unassigned and not is_orphan and not already_mine:
            # Otro mozo ya es dueño. Claim → 409; confirmar-al-marchar → no-op.
            if conflict_raises:
                raise TableAlreadyAssigned()
            return session
        session.assign_waiter(waiter_id)
        await self._sessions.save(session)
        # Estampar las órdenes vivas: el aviso "listo" (Fase 1) usa order.waiter_id.
        for order in await self._orders.list_open_by_session(tenant_id, session_id):
            if order.waiter_id != waiter_id:
                order.waiter_id = waiter_id
                await self._orders.save(order)
        return session


async def close_session_if_idle(
    sessions: TableSessionRepository,
    orders: OrderRepository,
    tenant_id: str,
    table_id: str,
    now: datetime,
) -> bool:
    """When a table's LAST live order ends (paid / cancelled), the visit is
    over: close its open session so the floor shows the table free again —
    otherwise "Abierta" would linger forever. Returns True if it closed one."""
    session = await sessions.get_open_by_table(tenant_id, table_id)
    if session is None:
        return False
    active = await orders.list_active(tenant_id)
    if any(o.table_id == table_id for o in active):
        return False
    session.close(now)
    await sessions.save(session)
    return True


class CloseSession:
    """Staff closes a table by hand (opened by mistake, party left without
    ordering). Refuses while a live order exists — pay or cancel it first."""

    def __init__(
        self,
        sessions: TableSessionRepository,
        orders: OrderRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._sessions = sessions
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, session_id: str) -> TableSession:
        self._tenant_context.set(tenant_id)
        session = await self._sessions.get_by_id(tenant_id, session_id)
        if session is None:
            raise SessionNotFound()
        active = await self._orders.list_active(tenant_id)
        if any(o.table_id == session.table_id for o in active):
            raise SessionHasActiveOrders()
        session.close(utcnow())
        await self._sessions.save(session)
        return session
