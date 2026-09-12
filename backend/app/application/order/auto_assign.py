from __future__ import annotations

from app.domain.identity.ports import TenantContext
from app.domain.table_session.repository import TableSessionRepository
from app.domain.timeclock.repository import ShiftRepository
from app.domain.user.repository import UserRepository
from app.domain.user.value_objects import Role


class AutoAssignWaiter:
    """Pick the waiter to own a table (Fase 3, Self-service).

    Least-loaded round-robin: among the waiters currently **on shift** (clocked-in),
    choose the one with the fewest open tables. Ties break by ``user_id`` so it's
    deterministic. Returns ``None`` when no waiter is on shift — the caller marches
    the paid order anyway and leaves it orphan (a waiter claims it later)."""

    def __init__(
        self,
        shifts: ShiftRepository,
        users: UserRepository,
        sessions: TableSessionRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._shifts = shifts
        self._users = users
        self._sessions = sessions
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> str | None:
        self._tenant_context.set(tenant_id)
        candidate_ids = {s.user_id for s in await self._shifts.list_open(tenant_id)}
        if not candidate_ids:
            return None
        roles = await self._users.roles_by_ids(tenant_id, candidate_ids)
        waiters = {uid for uid, role in roles.items() if role is Role.WAITER}
        if not waiters:
            return None
        load = {uid: 0 for uid in waiters}
        for session in await self._sessions.list_open(tenant_id):
            if session.waiter_id in load:
                load[session.waiter_id] += 1
        # menos mesas abiertas; empate → menor user_id (determinista)
        return min(waiters, key=lambda uid: (load[uid], uid))
