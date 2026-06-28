from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.order.entities import Order, OrderItem
from app.domain.order.exceptions import (
    EmptyOrder,
    InvalidItemTransition,
    InvalidOrderTransition,
    ItemNotPending,
)
from app.domain.order.value_objects import ItemStatus, OrderStatus, Station
from app.domain.shared.money import Money

_NOW = datetime(2026, 6, 27, 12, 0, tzinfo=UTC)


def _order(currency: str = "ARS") -> Order:
    return Order(
        id=str(uuid4()),
        tenant_id="t1",
        table_id="tb1",
        waiter_id="w1",
        currency=currency,
    )


def _item(
    amount: int = 1500,
    quantity: int = 1,
    currency: str = "ARS",
    station: Station = Station.KITCHEN,
) -> OrderItem:
    return OrderItem(
        id=str(uuid4()),
        product_id="p1",
        name="Milanesa",
        unit_price=Money(amount, currency),
        quantity=quantity,
        station=station,
    )


def test_lifecycle_happy_path() -> None:
    order = _order()
    order.add_item(_item(1500, 2))
    order.add_item(_item(800, 1))
    assert order.total().amount == 3800
    assert order.status is OrderStatus.OPEN  # all items PENDING

    order.send_to_kitchen()
    assert order.status is OrderStatus.SENT
    order.start_preparing()
    assert order.status is OrderStatus.PREPARING
    order.mark_ready()
    assert order.status is OrderStatus.READY
    order.mark_served()
    assert order.status is OrderStatus.SERVED


def test_send_empty_order_rejected() -> None:
    with pytest.raises(EmptyOrder):
        _order().send_to_kitchen()


def test_invalid_transition_rejected() -> None:
    order = _order()
    order.add_item(_item())
    with pytest.raises(InvalidOrderTransition):
        order.mark_ready()  # nothing is PREPARING yet


def test_can_add_round_after_sent() -> None:
    """Adding a new round to an order already in service is the whole point."""
    order = _order()
    order.add_item(_item())
    order.march(_NOW)
    assert order.status is OrderStatus.SENT

    order.add_item(_item(900, 1))  # second round, PENDING
    assert order.status is OrderStatus.SENT  # still in service, not OPEN/SERVED
    pending = [it for it in order.items if it.status is ItemStatus.PENDING]
    assert len(pending) == 1


def test_cannot_add_item_after_paid() -> None:
    order = _order()
    order.add_item(_item())
    order.mark_paid()
    with pytest.raises(InvalidOrderTransition):
        order.add_item(_item())


def test_cancel_from_open() -> None:
    order = _order()
    order.add_item(_item())
    order.cancel()
    assert order.status is OrderStatus.CANCELLED
    with pytest.raises(InvalidOrderTransition):
        order.march(_NOW)


def test_march_sets_sent_at_and_status() -> None:
    order = _order()
    order.add_item(_item())
    marched = order.march(_NOW)
    assert len(marched) == 1
    assert marched[0].status is ItemStatus.SENT
    assert marched[0].sent_at == _NOW
    assert order.status is OrderStatus.SENT


def test_march_only_pending_items() -> None:
    order = _order()
    first = _item()
    order.add_item(first)
    order.march(_NOW)  # first → SENT
    second = _item(900, 1)
    order.add_item(second)  # PENDING
    marched = order.march(_NOW)  # only the second
    assert [it.id for it in marched] == [second.id]
    assert first.status is ItemStatus.SENT


def test_advance_item_bump_and_recall() -> None:
    order = _order()
    item = _item()
    order.add_item(item)
    order.march(_NOW)
    order.advance_item(item.id, "preparing", _NOW)
    assert item.status is ItemStatus.PREPARING
    order.advance_item(item.id, "ready", _NOW)
    assert item.status is ItemStatus.READY
    assert item.ready_at == _NOW
    # Recall un-bumps a too-early READY back to PREPARING.
    order.advance_item(item.id, "recall", _NOW)
    assert item.status is ItemStatus.PREPARING
    assert item.ready_at is None


def test_advance_item_invalid_action_or_state() -> None:
    order = _order()
    item = _item()
    order.add_item(item)
    order.march(_NOW)
    with pytest.raises(InvalidItemTransition):
        order.advance_item(item.id, "bogus", _NOW)
    with pytest.raises(InvalidItemTransition):
        order.advance_item(item.id, "ready", _NOW)  # still SENT, not PREPARING


def test_per_item_progress_keeps_order_in_progress() -> None:
    """Two items, only one advanced → order is not yet SERVED."""
    order = _order()
    a, b = _item(), _item(900, 1)
    order.add_item(a)
    order.add_item(b)
    order.march(_NOW)
    order.advance_item(a.id, "preparing", _NOW)
    assert order.status is OrderStatus.PREPARING
    order.advance_item(a.id, "ready", _NOW)
    order.advance_item(a.id, "served", _NOW)
    # b still SENT → order rolls up to SENT (least advanced), never SERVED.
    assert order.status is OrderStatus.SENT


def test_remove_only_pending_item() -> None:
    order = _order()
    item = _item()
    order.add_item(item)
    order.march(_NOW)
    with pytest.raises(ItemNotPending):
        order.remove_item(item.id)


def test_set_quantity_only_pending_item() -> None:
    order = _order()
    item = _item()
    order.add_item(item)
    order.march(_NOW)
    with pytest.raises(ItemNotPending):
        order.set_item_quantity(item.id, 3)


def test_total_excludes_cancelled_items() -> None:
    order = _order()
    keep = _item(1000, 1)
    drop = _item(2000, 1)
    order.add_item(keep)
    order.add_item(drop)
    drop.status = ItemStatus.CANCELLED
    assert order.total().amount == 1000


def test_station_is_snapshotted_on_item() -> None:
    order = _order()
    coffee = _item(500, 1, station=Station.BAR)
    order.add_item(coffee)
    assert order.items[0].station is Station.BAR


def test_transfer_to_changes_table() -> None:
    order = _order()
    order.add_item(_item())
    order.transfer_to("tb2")
    assert order.table_id == "tb2"


def test_cannot_transfer_paid_order() -> None:
    order = _order()
    order.add_item(_item())
    order.mark_paid()
    with pytest.raises(InvalidOrderTransition):
        order.transfer_to("tb2")


def test_merge_moves_items_and_closes_source() -> None:
    dst = _order()
    dst.add_item(_item(1000, 1))
    src = _order()
    src.table_id = "tb2"
    src.add_item(_item(500, 2))
    src.march(_NOW)  # source items already in service

    dst.merge_from(src)

    assert len(dst.items) == 2
    assert dst.total().amount == 2000  # 1000 + 2x500
    assert src.items == []
    assert src.status is OrderStatus.CANCELLED
    # The moved item kept its in-service status.
    assert any(it.status is ItemStatus.SENT for it in dst.items)


def test_cannot_merge_into_paid_destination() -> None:
    dst = _order()
    dst.add_item(_item())
    dst.mark_paid()
    src = _order()
    src.add_item(_item())
    with pytest.raises(InvalidOrderTransition):
        dst.merge_from(src)
