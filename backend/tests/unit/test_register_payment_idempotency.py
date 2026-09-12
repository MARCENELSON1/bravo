"""RegisterPayment idempotency (Carta QR F3 Tanda B): a replayed idempotency key
returns the already-created payment instead of charging a second time — the guard
against a diner double-tapping an online cobro."""

from __future__ import annotations

from app.application.payment.use_cases import RegisterPayment
from app.domain.order.entities import Order, OrderItem
from app.domain.payment.entities import Payment
from app.domain.shared.money import Money
from tests.fakes import FakeTenantContext


class _PendingGateway:
    """Online-like: leaves the charge PENDING (a real webhook would confirm)."""

    async def charge(self, *, payment: Payment) -> Payment:
        return payment


class _FakePayments:
    def __init__(self) -> None:
        self.by_id: dict[str, Payment] = {}
        self.by_key: dict[str, Payment] = {}

    async def get_by_idempotency_key(self, tenant_id: str, key: str) -> Payment | None:
        return self.by_key.get(key)

    async def add(self, payment: Payment) -> None:
        self.by_id[payment.id] = payment
        if payment.idempotency_key is not None:
            self.by_key[payment.idempotency_key] = payment

    async def list_by_order(self, tenant_id: str, order_id: str) -> list[Payment]:
        return [p for p in self.by_id.values() if p.order_id == order_id]

    async def save(self, payment: Payment) -> None:
        self.by_id[payment.id] = payment


class _FakeOrders:
    def __init__(self, order: Order) -> None:
        self._order = order

    async def get_by_id(self, tenant_id: str, order_id: str) -> Order | None:
        return self._order if order_id == self._order.id else None

    async def save(self, order: Order) -> None:
        self._order = order


def _order() -> Order:
    order = Order(id="o1", tenant_id="t1", table_id="tb1", waiter_id="w", currency="ARS")
    order.add_item(
        OrderItem(
            id="i1",
            product_id="p",
            name="Plato",
            unit_price=Money(1000000, "ARS"),
            quantity=1,
        )
    )
    return order


def _use_case(payments: _FakePayments, order: Order) -> RegisterPayment:
    return RegisterPayment(
        payments=payments,  # type: ignore[arg-type]
        orders=_FakeOrders(order),  # type: ignore[arg-type]
        gateway=_PendingGateway(),  # type: ignore[arg-type]
        tenant_context=FakeTenantContext(),
    )


async def test_same_key_replays_the_existing_payment() -> None:
    payments = _FakePayments()
    uc = _use_case(payments, _order())

    first = await uc.execute(
        tenant_id="t1", order_id="o1", method="MERCADOPAGO", amount=1000000, idempotency_key="k1"
    )
    second = await uc.execute(
        tenant_id="t1", order_id="o1", method="MERCADOPAGO", amount=1000000, idempotency_key="k1"
    )

    assert first.id == second.id
    assert len(payments.by_id) == 1  # only ONE charge created


async def test_different_keys_create_separate_payments() -> None:
    payments = _FakePayments()
    uc = _use_case(payments, _order())

    await uc.execute(
        tenant_id="t1", order_id="o1", method="MERCADOPAGO", amount=500000, idempotency_key="k1"
    )
    await uc.execute(
        tenant_id="t1", order_id="o1", method="MERCADOPAGO", amount=500000, idempotency_key="k2"
    )

    assert len(payments.by_id) == 2


async def test_no_key_keeps_parity_no_lookup() -> None:
    payments = _FakePayments()
    uc = _use_case(payments, _order())

    payment = await uc.execute(
        tenant_id="t1", order_id="o1", method="MERCADOPAGO", amount=1000000
    )

    assert payment.idempotency_key is None
    assert len(payments.by_id) == 1
