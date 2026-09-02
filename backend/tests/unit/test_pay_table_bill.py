"""Unit tests for PayTableBill / GetPublicPaymentStatus (Carta QR F3 Tanda B).

The gate, the order selection and the SERVER-COMPUTED amount are exercised with a
spy RegisterPayment (the real cobro engine is covered end-to-end elsewhere)."""

from __future__ import annotations

import pytest

from app.application.payment.pay_table_bill import GetPublicPaymentStatus, PayTableBill
from app.domain.order.entities import Order, OrderItem
from app.domain.order.value_objects import ItemStatus, OrderStatus
from app.domain.payment.entities import Payment
from app.domain.payment.exceptions import (
    InvalidPaymentAmount,
    NothingToPay,
    PaymentNotFound,
    SelfPayDisabled,
)
from app.domain.payment.self_pay_settings import SelfPaySettings
from app.domain.payment.value_objects import (
    PaymentDirection,
    PaymentMethod,
    PaymentStatus,
)
from app.domain.public_menu.exceptions import InvalidTableQrToken
from app.domain.shared.money import Money
from app.domain.table_session.entities import TableSession
from app.infrastructure.public_menu.signed_table_qr import HmacTableQrToken
from tests.fakes import FakeTenantContext

_SECRET = "s3cr3t"


class _FakeSessions:
    def __init__(self, session: TableSession | None) -> None:
        self._session = session

    async def get_open_by_table(self, tenant_id: str, table_id: str) -> TableSession | None:
        return self._session


class _FakeOrders:
    def __init__(self, orders: list[Order]) -> None:
        self._orders = orders

    async def list_open_by_session(self, tenant_id: str, session_id: str) -> list[Order]:
        return list(self._orders)


class _FakePayments:
    def __init__(self, by_order: dict[str, list[Payment]]) -> None:
        self._by_order = by_order
        self.by_id: dict[str, Payment] = {}

    async def list_by_order(self, tenant_id: str, order_id: str) -> list[Payment]:
        return self._by_order.get(order_id, [])

    async def get_by_id(self, tenant_id: str, payment_id: str) -> Payment | None:
        return self.by_id.get(payment_id)


class _FakeSettings:
    def __init__(self, settings: SelfPaySettings) -> None:
        self._settings = settings

    async def get(self, tenant_id: str) -> SelfPaySettings:
        return self._settings


class _SpyRegisterPayment:
    """Records the cobro it was asked to run and returns a canned confirmed payment."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def execute(
        self,
        *,
        tenant_id: str,
        order_id: str,
        method: str,
        amount: int,
        tip: int = 0,
        idempotency_key: str | None = None,
        return_url: str | None = None,
    ) -> Payment:
        self.calls.append(
            {
                "order_id": order_id,
                "method": method,
                "amount": amount,
                "tip": tip,
                "idempotency_key": idempotency_key,
                "return_url": return_url,
            }
        )
        return Payment(
            id="pay-1",
            tenant_id=tenant_id,
            direction=PaymentDirection.INFLOW,
            amount=Money(amount, "ARS"),
            method=PaymentMethod(method),
            status=PaymentStatus.CONFIRMED,
            order_id=order_id,
            tip_amount=tip,
        )


def _item(price: int, qty: int, status: ItemStatus = ItemStatus.SENT) -> OrderItem:
    return OrderItem(
        id=f"i-{price}-{qty}",
        product_id="p",
        name="Plato",
        unit_price=Money(price, "ARS"),
        quantity=qty,
        status=status,
    )


def _order(order_id: str, items: list[OrderItem]) -> Order:
    return Order(
        id=order_id,
        tenant_id="t1",
        table_id="tbl-1",
        waiter_id="w",
        currency="ARS",
        status=OrderStatus.SENT,
        items=items,
        session_id="sess-1",
    )


def _inflow(amount: int, order_id: str) -> Payment:
    return Payment(
        id=f"paid-{order_id}-{amount}",
        tenant_id="t1",
        direction=PaymentDirection.INFLOW,
        amount=Money(amount, "ARS"),
        method=PaymentMethod.CASH,
        status=PaymentStatus.CONFIRMED,
        order_id=order_id,
    )


def _use_case(
    *,
    session: TableSession | None,
    orders: list[Order],
    payments: dict[str, list[Payment]],
    settings: SelfPaySettings,
) -> tuple[PayTableBill, HmacTableQrToken, _SpyRegisterPayment]:
    token = HmacTableQrToken(secret=_SECRET)
    spy = _SpyRegisterPayment()
    uc = PayTableBill(
        token=token,
        settings=_FakeSettings(settings),  # type: ignore[arg-type]
        sessions=_FakeSessions(session),  # type: ignore[arg-type]
        orders=_FakeOrders(orders),  # type: ignore[arg-type]
        payments=_FakePayments(payments),  # type: ignore[arg-type]
        register_payment=spy,  # type: ignore[arg-type]
        tenant_context=FakeTenantContext(),
        app_base_url="https://app.wellnod.test",
    )
    return uc, token, spy


async def test_charges_the_server_computed_remaining_balance() -> None:
    orders = [_order("o1", [_item(1000000, 2)])]  # total 2_000_000
    payments = {"o1": [_inflow(500000, "o1")]}  # already paid 500k → balance 1.5M
    uc, token, spy = _use_case(
        session=TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1"),
        orders=orders,
        payments=payments,
        settings=SelfPaySettings(enabled=True),
    )

    result = await uc.execute(token=token.issue("t1", "tbl-1"))

    assert spy.calls[0]["amount"] == 1_500_000  # server-computed, not from the client
    assert spy.calls[0]["method"] == PaymentMethod.MERCADOPAGO.value
    assert result.order_id == "o1"
    assert result.status == "CONFIRMED"


async def test_charges_the_oldest_unpaid_order_first() -> None:
    orders = [
        _order("o1", [_item(1000000, 1)]),  # 1M, fully paid below
        _order("o2", [_item(700000, 1)]),  # 700k, unpaid → this is the target
    ]
    payments = {"o1": [_inflow(1000000, "o1")]}
    uc, token, spy = _use_case(
        session=TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1"),
        orders=orders,
        payments=payments,
        settings=SelfPaySettings(enabled=True),
    )

    await uc.execute(token=token.issue("t1", "tbl-1"))

    assert spy.calls[0]["order_id"] == "o2"
    assert spy.calls[0]["amount"] == 700000


async def test_passes_a_return_url_back_to_the_table_menu() -> None:
    orders = [_order("o1", [_item(1000000, 1)])]
    uc, token, spy = _use_case(
        session=TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1"),
        orders=orders,
        payments={},
        settings=SelfPaySettings(enabled=True),
    )

    issued = token.issue("t1", "tbl-1")
    await uc.execute(token=issued)

    # MercadoPago sends the diner back to THEIR table's QR menu after paying.
    assert spy.calls[0]["return_url"] == f"https://app.wellnod.test/carta/{issued}"


async def test_partial_amount_splits_the_bill() -> None:
    orders = [_order("o1", [_item(1000000, 2)])]  # balance 2_000_000
    uc, token, spy = _use_case(
        session=TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1"),
        orders=orders,
        payments={},
        settings=SelfPaySettings(enabled=True),
    )

    await uc.execute(token=token.issue("t1", "tbl-1"), amount=500000)

    assert spy.calls[0]["amount"] == 500000  # only my part, not the whole balance


async def test_amount_over_balance_rejected() -> None:
    orders = [_order("o1", [_item(1000000, 1)])]  # balance 1_000_000
    uc, token, spy = _use_case(
        session=TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1"),
        orders=orders,
        payments={},
        settings=SelfPaySettings(enabled=True),
    )
    with pytest.raises(InvalidPaymentAmount):
        await uc.execute(token=token.issue("t1", "tbl-1"), amount=1500000)
    assert spy.calls == []  # a tampered client can't overpay


async def test_amount_zero_rejected() -> None:
    orders = [_order("o1", [_item(1000000, 1)])]
    uc, token, _spy = _use_case(
        session=TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1"),
        orders=orders,
        payments={},
        settings=SelfPaySettings(enabled=True),
    )
    with pytest.raises(InvalidPaymentAmount):
        await uc.execute(token=token.issue("t1", "tbl-1"), amount=0)


async def test_tip_rides_when_enabled_and_passes_idempotency_key() -> None:
    orders = [_order("o1", [_item(1000000, 1)])]
    uc, token, spy = _use_case(
        session=TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1"),
        orders=orders,
        payments={},
        settings=SelfPaySettings(enabled=True, tips_enabled=True),
    )

    result = await uc.execute(token=token.issue("t1", "tbl-1"), tip=150000, idempotency_key="k1")

    assert spy.calls[0]["tip"] == 150000
    assert spy.calls[0]["idempotency_key"] == "k1"
    assert result.tip == 150000


async def test_tip_is_dropped_when_owner_disabled_tips() -> None:
    orders = [_order("o1", [_item(1000000, 1)])]
    uc, token, spy = _use_case(
        session=TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1"),
        orders=orders,
        payments={},
        settings=SelfPaySettings(enabled=True, tips_enabled=False),
    )

    await uc.execute(token=token.issue("t1", "tbl-1"), tip=150000)

    assert spy.calls[0]["tip"] == 0  # never charge a tip the owner turned off


async def test_negative_tip_rejected() -> None:
    orders = [_order("o1", [_item(1000000, 1)])]
    uc, token, _spy = _use_case(
        session=TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1"),
        orders=orders,
        payments={},
        settings=SelfPaySettings(enabled=True),
    )
    with pytest.raises(InvalidPaymentAmount):
        await uc.execute(token=token.issue("t1", "tbl-1"), tip=-1)


async def test_self_pay_disabled_rejected() -> None:
    orders = [_order("o1", [_item(1000000, 1)])]
    uc, token, spy = _use_case(
        session=TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1"),
        orders=orders,
        payments={},
        settings=SelfPaySettings(enabled=False),
    )
    with pytest.raises(SelfPayDisabled):
        await uc.execute(token=token.issue("t1", "tbl-1"))
    assert spy.calls == []  # nothing charged


async def test_no_open_session_is_nothing_to_pay() -> None:
    uc, token, _spy = _use_case(
        session=None,
        orders=[],
        payments={},
        settings=SelfPaySettings(enabled=True),
    )
    with pytest.raises(NothingToPay):
        await uc.execute(token=token.issue("t1", "tbl-1"))


async def test_all_orders_settled_is_nothing_to_pay() -> None:
    orders = [_order("o1", [_item(1000000, 1)])]
    payments = {"o1": [_inflow(1000000, "o1")]}  # fully paid
    uc, token, _spy = _use_case(
        session=TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1"),
        orders=orders,
        payments=payments,
        settings=SelfPaySettings(enabled=True),
    )
    with pytest.raises(NothingToPay):
        await uc.execute(token=token.issue("t1", "tbl-1"))


async def test_bad_token_rejected() -> None:
    uc, _token, spy = _use_case(
        session=None,
        orders=[],
        payments={},
        settings=SelfPaySettings(enabled=True),
    )
    with pytest.raises(InvalidTableQrToken):
        await uc.execute(token="garbage.deadbeef")
    assert spy.calls == []


async def test_payment_status_scoped_by_token() -> None:
    token = HmacTableQrToken(secret=_SECRET)
    payments = _FakePayments({})
    payments.by_id["pay-1"] = Payment(
        id="pay-1",
        tenant_id="t1",
        direction=PaymentDirection.INFLOW,
        amount=Money(500000, "ARS"),
        method=PaymentMethod.MERCADOPAGO,
        status=PaymentStatus.PENDING,
        order_id="o1",
        tip_amount=20000,
    )
    uc = GetPublicPaymentStatus(
        token=token,
        payments=payments,  # type: ignore[arg-type]
        tenant_context=FakeTenantContext(),
    )

    payment = await uc.execute(token=token.issue("t1", "tbl-1"), payment_id="pay-1")
    assert payment.status is PaymentStatus.PENDING
    assert payment.tip_amount == 20000

    with pytest.raises(PaymentNotFound):
        await uc.execute(token=token.issue("t1", "tbl-1"), payment_id="nope")
