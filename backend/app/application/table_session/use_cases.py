from __future__ import annotations

from uuid import uuid4

from app.application.clock import utcnow
from app.domain.identity.ports import TenantContext
from app.domain.table.exceptions import TableNotFound
from app.domain.table.repository import TableRepository
from app.domain.table_session.entities import TableSession
from app.domain.table_session.exceptions import SessionNotFound
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
