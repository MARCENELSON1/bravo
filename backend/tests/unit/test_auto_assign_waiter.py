from __future__ import annotations

from types import SimpleNamespace

from app.application.order.auto_assign import AutoAssignWaiter
from app.domain.user.value_objects import Role
from tests.fakes import FakeTenantContext


class _FakeShifts:
    def __init__(self, user_ids: list[str]) -> None:
        self._ids = user_ids

    async def list_open(self, tenant_id: str):
        return [SimpleNamespace(user_id=u) for u in self._ids]


class _FakeUsers:
    def __init__(self, roles: dict[str, Role]) -> None:
        self._roles = roles

    async def roles_by_ids(self, tenant_id: str, ids: set[str]) -> dict[str, Role]:
        return {u: r for u, r in self._roles.items() if u in ids}


class _FakeSessions:
    def __init__(self, waiter_ids: list[str | None]) -> None:
        self._w = waiter_ids

    async def list_open(self, tenant_id: str):
        return [SimpleNamespace(waiter_id=w) for w in self._w]


def _uc(shift_ids, roles, session_waiters) -> AutoAssignWaiter:
    return AutoAssignWaiter(
        shifts=_FakeShifts(shift_ids),
        users=_FakeUsers(roles),
        sessions=_FakeSessions(session_waiters),
        tenant_context=FakeTenantContext(),
    )


async def test_picks_least_loaded_waiter() -> None:
    roles = {"w1": Role.WAITER, "w2": Role.WAITER}
    uc = _uc(["w1", "w2"], roles, ["w1", "w1"])  # w1 con 2 mesas, w2 con 0
    assert await uc.execute(tenant_id="t1") == "w2"


async def test_ignores_non_waiters() -> None:
    roles = {"m1": Role.MANAGER, "w1": Role.WAITER}
    uc = _uc(["m1", "w1"], roles, [])
    assert await uc.execute(tenant_id="t1") == "w1"


async def test_none_when_no_waiter_clocked_in() -> None:
    uc = _uc(["m1"], {"m1": Role.MANAGER}, [])
    assert await uc.execute(tenant_id="t1") is None


async def test_none_when_nobody_clocked_in() -> None:
    uc = _uc([], {}, [])
    assert await uc.execute(tenant_id="t1") is None


async def test_tie_breaks_deterministically_by_user_id() -> None:
    roles = {"wb": Role.WAITER, "wa": Role.WAITER}  # ambos 0 mesas → menor id "wa"
    uc = _uc(["wb", "wa"], roles, [])
    assert await uc.execute(tenant_id="t1") == "wa"


async def test_ignores_orphan_sessions_in_load() -> None:
    roles = {"w1": Role.WAITER}
    # sesiones huérfanas (None / sentinel) no cuentan como carga de nadie
    uc = _uc(["w1"], roles, [None, "00000000-0000-0000-0000-000000000000"])
    assert await uc.execute(tenant_id="t1") == "w1"
