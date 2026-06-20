from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.order.entities import Order, OrderItem
from app.domain.order.exceptions import EmptyOrder, InvalidOrderTransition
from app.domain.order.value_objects import OrderStatus
from app.domain.shared.money import Money


def _order(currency: str = "ARS") -> Order:
    return Order(
        id=str(uuid4()),
        tenant_id="t1",
        table_id="tb1",
        waiter_id="w1",
        currency=currency,
    )


def _item(amount: int = 1500, quantity: int = 1, currency: str = "ARS") -> OrderItem:
    return OrderItem(
        id=str(uuid4()),
        product_id="p1",
        name="Milanesa",
        unit_price=Money(amount, currency),
        quantity=quantity,
    )


def test_lifecycle_happy_path() -> None:
    order = _order()
    order.add_item(_item(1500, 2))
    order.add_item(_item(800, 1))
    assert order.total().amount == 3800

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
        order.mark_ready()  # OPEN -> READY is invalid


def test_cannot_add_item_after_sent() -> None:
    order = _order()
    order.add_item(_item())
    order.send_to_kitchen()
    with pytest.raises(InvalidOrderTransition):
        order.add_item(_item())


def test_cancel_from_open() -> None:
    order = _order()
    order.add_item(_item())
    order.cancel()
    assert order.status is OrderStatus.CANCELLED
