"""Unit: derived live state of a table session (the floor's status engine)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.order.entities import Order, OrderItem
from app.domain.order.value_objects import ItemStatus, OrderStatus, Station
from app.domain.shared.money import Money
from app.domain.table_session.entities import TableSession
from app.domain.table_session.status import derive_session_state
from app.domain.table_session.value_objects import SessionStatus

_T0 = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _session(**kw) -> TableSession:
    return TableSession(
        id="s1", tenant_id="t1", table_id="tb1", opened_at=_T0, **kw
    )


def _item(status: ItemStatus, *, sent_at=None, ready_at=None) -> OrderItem:
    return OrderItem(
        id=f"i-{status.value}-{sent_at}-{ready_at}",
        product_id="p1",
        name="Milanesa",
        unit_price=Money(1000, "ARS"),
        quantity=1,
        station=Station.KITCHEN,
        status=status,
        sent_at=sent_at,
        ready_at=ready_at,
    )


def _order(items: list[OrderItem], status=OrderStatus.SENT) -> Order:
    return Order(
        id="o1", tenant_id="t1", table_id="tb1", waiter_id="w1",
        currency="ARS", status=status, items=items,
    )


def test_open_when_no_marched_items():
    d = derive_session_state(_session(), [_order([_item(ItemStatus.PENDING)], OrderStatus.OPEN)])
    assert d.status is SessionStatus.OPEN
    assert d.since == _T0


def test_open_when_no_orders():
    d = derive_session_state(_session(), [])
    assert d.status is SessionStatus.OPEN


def test_in_kitchen_uses_oldest_sent_at():
    a = _T0 + timedelta(minutes=1)
    b = _T0 + timedelta(minutes=3)
    d = derive_session_state(
        _session(),
        [_order([_item(ItemStatus.SENT, sent_at=b), _item(ItemStatus.PREPARING, sent_at=a)])],
    )
    assert d.status is SessionStatus.IN_KITCHEN
    assert d.since == a  # oldest ticket in the kitchen


def test_to_serve_uses_oldest_ready_at():
    a = _T0 + timedelta(minutes=5)
    b = _T0 + timedelta(minutes=8)
    d = derive_session_state(
        _session(),
        [_order([_item(ItemStatus.READY, ready_at=b), _item(ItemStatus.READY, ready_at=a)])],
    )
    assert d.status is SessionStatus.TO_SERVE
    assert d.since == a  # the dish that's been sitting longest


def test_to_serve_beats_in_kitchen_precedence():
    """A single ready dish wins even while others still cook — it's getting cold."""
    d = derive_session_state(
        _session(),
        [_order([
            _item(ItemStatus.READY, ready_at=_T0 + timedelta(minutes=4)),
            _item(ItemStatus.PREPARING, sent_at=_T0),
        ])],
    )
    assert d.status is SessionStatus.TO_SERVE


def test_served_when_all_served_and_no_bill():
    d = derive_session_state(
        _session(), [_order([_item(ItemStatus.SERVED)], OrderStatus.SERVED)]
    )
    assert d.status is SessionStatus.SERVED
    assert d.since == _T0


def test_to_charge_when_bill_requested():
    billed = _T0 + timedelta(minutes=40)
    d = derive_session_state(
        _session(bill_requested_at=billed),
        [_order([_item(ItemStatus.SERVED)], OrderStatus.SERVED)],
    )
    assert d.status is SessionStatus.TO_CHARGE
    assert d.since == billed


def test_to_serve_beats_bill_requested():
    """para_servir is MÁXIMA PRIORIDAD: serve the ready dish, then charge."""
    d = derive_session_state(
        _session(bill_requested_at=_T0 + timedelta(minutes=40)),
        [_order([_item(ItemStatus.READY, ready_at=_T0 + timedelta(minutes=5))])],
    )
    assert d.status is SessionStatus.TO_SERVE


def test_bill_requested_beats_in_kitchen():
    d = derive_session_state(
        _session(bill_requested_at=_T0 + timedelta(minutes=40)),
        [_order([_item(ItemStatus.PREPARING, sent_at=_T0)])],
    )
    assert d.status is SessionStatus.TO_CHARGE


def test_cancelled_order_items_ignored():
    d = derive_session_state(
        _session(),
        [_order([_item(ItemStatus.READY, ready_at=_T0)], OrderStatus.CANCELLED)],
    )
    assert d.status is SessionStatus.OPEN  # cancelled order → no active items


def test_cancelled_item_ignored():
    d = derive_session_state(
        _session(),
        [_order([_item(ItemStatus.CANCELLED), _item(ItemStatus.SERVED)], OrderStatus.SERVED)],
    )
    assert d.status is SessionStatus.SERVED


def test_new_round_after_served_returns_to_open():
    """A fresh unmarched item added after a served round → back to abierta."""
    d = derive_session_state(
        _session(),
        [_order([_item(ItemStatus.SERVED), _item(ItemStatus.PENDING)], OrderStatus.SENT)],
    )
    assert d.status is SessionStatus.OPEN


def test_to_charge_needs_something_to_charge():
    # Se pidió la cuenta pero la mesa no tiene nada pedido (se anuló todo, o
    # fue un toque por error): no puede quedar trabada en "a cobrar" con $0.
    bill = _T0 + timedelta(minutes=5)
    d = derive_session_state(_session(bill_requested_at=bill), [])
    assert d.status is SessionStatus.OPEN

    d = derive_session_state(
        _session(bill_requested_at=bill), [_order([], OrderStatus.OPEN)]
    )
    assert d.status is SessionStatus.OPEN


def test_to_charge_when_bill_requested_with_items():
    bill = _T0 + timedelta(minutes=5)
    d = derive_session_state(
        _session(bill_requested_at=bill),
        [_order([_item(ItemStatus.SERVED)], OrderStatus.SERVED)],
    )
    assert d.status is SessionStatus.TO_CHARGE
    assert d.since == bill
