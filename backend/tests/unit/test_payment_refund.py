from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.payment.entities import Payment
from app.domain.payment.exceptions import PaymentNotRefundable
from app.domain.payment.value_objects import PaymentDirection, PaymentMethod, PaymentStatus
from app.domain.shared.money import Money


def _payment(status: PaymentStatus) -> Payment:
    return Payment(
        id=str(uuid4()),
        tenant_id="t1",
        direction=PaymentDirection.INFLOW,
        amount=Money(30000, "ARS"),
        method=PaymentMethod.CASH,
        status=status,
        order_id="o1",
    )


def test_refund_confirmed_payment() -> None:
    payment = _payment(PaymentStatus.CONFIRMED)
    payment.refund()
    assert payment.status is PaymentStatus.REFUNDED


def test_cannot_refund_pending_payment() -> None:
    with pytest.raises(PaymentNotRefundable):
        _payment(PaymentStatus.PENDING).refund()


def test_cannot_refund_twice() -> None:
    payment = _payment(PaymentStatus.CONFIRMED)
    payment.refund()
    with pytest.raises(PaymentNotRefundable):
        payment.refund()
