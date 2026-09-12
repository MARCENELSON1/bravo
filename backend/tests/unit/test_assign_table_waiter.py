from __future__ import annotations

import pytest

from app.application.table_session.use_cases import AssignTableWaiter
from app.domain.order.entities import Order
from app.domain.order.value_objects import CUSTOMER_WAITER_ID
from app.domain.table_session.entities import TableSession
from app.domain.table_session.exceptions import TableAlreadyAssigned
from tests.fakes import FakeTenantContext


class _FakeSessions:
    def __init__(self, session: TableSession) -> None:
        self._s = {session.id: session}

    async def get_by_id(self, tenant_id: str, session_id: str) -> TableSession | None:
        return self._s.get(session_id)

    async def save(self, session: TableSession) -> None:
        self._s[session.id] = session


class _FakeOrders:
    def __init__(self, orders: list[Order]) -> None:
        self._orders = {o.id: o for o in orders}

    async def list_open_by_session(self, tenant_id: str, session_id: str) -> list[Order]:
        return [o for o in self._orders.values() if o.session_id == session_id]

    async def save(self, order: Order) -> None:
        self._orders[order.id] = order


def _session(waiter_id: str | None = None) -> TableSession:
    return TableSession(id="s1", tenant_id="t1", table_id="tb1", waiter_id=waiter_id)


def _order(waiter_id: str = CUSTOMER_WAITER_ID) -> Order:
    return Order(
        id="o1", tenant_id="t1", table_id="tb1",
        waiter_id=waiter_id, currency="ARS", session_id="s1",
    )


def _uc(session: TableSession, orders: list[Order]) -> tuple[AssignTableWaiter, _FakeOrders]:
    fake_orders = _FakeOrders(orders)
    uc = AssignTableWaiter(
        sessions=_FakeSessions(session),
        orders=fake_orders,
        tenant_context=FakeTenantContext(),
    )
    return uc, fake_orders


async def test_assigns_session_and_stamps_live_orders() -> None:
    uc, orders = _uc(_session(waiter_id=None), [_order()])
    out = await uc.execute(tenant_id="t1", session_id="s1", waiter_id="w9")
    assert out.waiter_id == "w9"
    # el aviso "listo" usa order.waiter_id → debe quedar estampado
    assert (await orders.list_open_by_session("t1", "s1"))[0].waiter_id == "w9"


async def test_qr_sentinel_counts_as_orphan() -> None:
    uc, _ = _uc(_session(waiter_id=CUSTOMER_WAITER_ID), [_order()])
    out = await uc.execute(
        tenant_id="t1", session_id="s1", waiter_id="w9", only_if_unassigned=True
    )
    assert out.waiter_id == "w9"


async def test_claim_conflict_when_owned_by_other() -> None:
    uc, _ = _uc(_session(waiter_id="wA"), [_order(waiter_id="wA")])
    with pytest.raises(TableAlreadyAssigned):
        await uc.execute(
            tenant_id="t1", session_id="s1", waiter_id="wB",
            only_if_unassigned=True, conflict_raises=True,
        )


async def test_confirm_is_noop_when_owned_by_other() -> None:
    uc, orders = _uc(_session(waiter_id="wA"), [_order(waiter_id="wA")])
    out = await uc.execute(
        tenant_id="t1", session_id="s1", waiter_id="wB",
        only_if_unassigned=True, conflict_raises=False,
    )
    assert out.waiter_id == "wA"  # no roba la mesa
    assert (await orders.list_open_by_session("t1", "s1"))[0].waiter_id == "wA"


async def test_manager_reassign_forces_new_owner() -> None:
    uc, orders = _uc(_session(waiter_id="wA"), [_order(waiter_id="wA")])
    out = await uc.execute(tenant_id="t1", session_id="s1", waiter_id="wB")
    assert out.waiter_id == "wB"
    assert (await orders.list_open_by_session("t1", "s1"))[0].waiter_id == "wB"
