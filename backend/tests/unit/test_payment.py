from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.order.entities import Order, OrderItem
from app.domain.order.exceptions import InvalidOrderTransition
from app.domain.order.value_objects import OrderStatus
from app.domain.payment.entities import Payment
from app.domain.payment.value_objects import PaymentDirection, PaymentMethod, PaymentStatus
from app.domain.shared.money import Money


def _order() -> Order:
    order = Order(
        id=str(uuid4()), tenant_id="t1", table_id="tb1", waiter_id="w1", currency="ARS"
    )
    order.add_item(
        OrderItem(
            id=str(uuid4()),
            product_id="p1",
            name="Milanesa",
            unit_price=Money(1500, "ARS"),
            quantity=2,
        )
    )
    return order


def test_order_mark_paid() -> None:
    order = _order()
    order.mark_paid()
    assert order.status is OrderStatus.PAID


def test_order_mark_paid_twice_rejected() -> None:
    order = _order()
    order.mark_paid()
    with pytest.raises(InvalidOrderTransition):
        order.mark_paid()


def test_order_mark_paid_when_cancelled_rejected() -> None:
    order = _order()
    order.cancel()
    with pytest.raises(InvalidOrderTransition):
        order.mark_paid()


def test_payment_confirm() -> None:
    payment = Payment(
        id="1",
        tenant_id="t1",
        direction=PaymentDirection.INFLOW,
        amount=Money(1000, "ARS"),
        method=PaymentMethod.CASH,
        status=PaymentStatus.PENDING,
        order_id="o1",
    )
    payment.confirm()
    assert payment.status is PaymentStatus.CONFIRMED
