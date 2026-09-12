"""Cobrar avisa al plano.

Era el único cambio de estado de una mesa que NO publicaba ``floor.changed``: el
resto del flujo (abrir, marchar, mover, servir) sí lo hace. Como consecuencia, la
transición pagado→libre la veía solo el poll del cliente — y por eso el plano
tenía que repreguntar 3× más seguido que las demás pantallas, para siempre.

Molde: tests/unit/test_register_payment_idempotency.py (fakes + spy bus).
"""

from __future__ import annotations

from app.application.payment.use_cases import RegisterPayment
from app.domain.order.entities import Order, OrderItem
from app.domain.payment.entities import Payment
from app.domain.realtime.ports import DomainEvent
from app.domain.shared.money import Money
from tests.fakes import FakeTenantContext


class _ConfirmingGateway:
    """Como el manual (efectivo): la plata ya se movió, confirma en el acto."""

    async def charge(self, *, payment: Payment) -> Payment:
        payment.confirm()
        return payment


class _FakePayments:
    def __init__(self) -> None:
        self.by_id: dict[str, Payment] = {}

    async def get_by_idempotency_key(self, tenant_id: str, key: str) -> Payment | None:
        return None

    async def add(self, payment: Payment) -> None:
        self.by_id[payment.id] = payment

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


class _SpyBus:
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.published.append(event)


def _order() -> Order:
    order = Order(id="o1", tenant_id="t1", table_id="tb1", waiter_id="w", currency="ARS")
    order.add_item(
        OrderItem(id="i1", product_id="p", name="Plato", unit_price=Money(1000, "ARS"), quantity=1)
    )
    return order


def _use_case(payments: _FakePayments, order: Order, bus: _SpyBus | None) -> RegisterPayment:
    return RegisterPayment(
        payments=payments,  # type: ignore[arg-type]
        orders=_FakeOrders(order),  # type: ignore[arg-type]
        gateway=_ConfirmingGateway(),  # type: ignore[arg-type]
        tenant_context=FakeTenantContext(),
        event_bus=bus,  # type: ignore[arg-type]
    )


async def test_settling_an_order_publishes_floor_changed() -> None:
    bus = _SpyBus()
    uc = _use_case(_FakePayments(), _order(), bus)

    await uc.execute(tenant_id="t1", order_id="o1", method="CASH", amount=1000)

    floor = [e for e in bus.published if e.type == "floor.changed"]
    assert len(floor) == 1, "el plano se entera del cobro por evento, no por el poll"
    assert floor[0].tenant_id == "t1"
    assert floor[0].payload["table_id"] == "tb1"


async def test_a_partial_payment_publishes_nothing() -> None:
    """Solo la transición a PAID mueve el plano; un pago que no cubre el total, no.

    Sin esto el evento saldría en cada cobro parcial de una cuenta dividida, y el
    plano se repreguntaría entero por cada uno.
    """
    bus = _SpyBus()
    uc = _use_case(_FakePayments(), _order(), bus)

    await uc.execute(tenant_id="t1", order_id="o1", method="CASH", amount=400)

    assert [e for e in bus.published if e.type == "floor.changed"] == []


async def test_settling_twice_publishes_once() -> None:
    """Cubierto el total, un cobro extra no vuelve a avisar: la orden ya está PAID."""
    bus = _SpyBus()
    payments = _FakePayments()
    order = _order()
    uc = _use_case(payments, order, bus)

    await uc.execute(tenant_id="t1", order_id="o1", method="CASH", amount=1000)
    await uc.execute(tenant_id="t1", order_id="o1", method="CASH", amount=1000)

    assert len([e for e in bus.published if e.type == "floor.changed"]) == 1


async def test_without_a_bus_the_cobro_still_works() -> None:
    """El aviso es opcional y fire-and-forget: nunca puede hacer fallar un cobro."""
    payments = _FakePayments()
    order = _order()
    uc = _use_case(payments, order, None)

    payment = await uc.execute(tenant_id="t1", order_id="o1", method="CASH", amount=1000)

    assert payment.id in payments.by_id
