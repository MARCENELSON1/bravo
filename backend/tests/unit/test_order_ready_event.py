"""El caso de uso emite un único `order.ready` cuando la orden entera queda READY
(no en cada ítem). Molde: tests/unit/test_table_attention.py (spy bus + fakes)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.application.order.use_cases import AdvanceItem, AdvanceOrder
from app.domain.order.entities import Order, OrderItem
from app.domain.order.value_objects import Station
from app.domain.realtime.ports import DomainEvent
from app.domain.shared.money import Money
from app.domain.table.entities import Table
from tests.fakes import FakeTenantContext

_NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)


class _FakeOrders:
    def __init__(self, order: Order) -> None:
        self._order = order

    async def get_by_id(self, tenant_id: str, order_id: str) -> Order | None:
        return self._order

    async def save(self, order: Order) -> None:
        return None


class _FakeTables:
    def __init__(self, table: Table | None) -> None:
        self._table = table

    async def get_by_id(self, tenant_id: str, table_id: str) -> Table | None:
        return self._table


class _SpyBus:
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.published.append(event)


def _item(name: str = "Milanesa") -> OrderItem:
    return OrderItem(
        id=str(uuid4()),
        product_id="p1",
        name=name,
        unit_price=Money(1500, "ARS"),
        quantity=1,
        station=Station.KITCHEN,
    )


def _sent_order(*items: OrderItem) -> Order:
    order = Order(id=str(uuid4()), tenant_id="t1", table_id="tb1",
                  waiter_id="w1", currency="ARS")
    for it in items:
        order.add_item(it)
    order.send_to_kitchen()  # todos -> SENT
    return order


def _advance_item_uc(order: Order, table: Table | None) -> tuple[AdvanceItem, _SpyBus]:
    bus = _SpyBus()
    uc = AdvanceItem(
        orders=_FakeOrders(order),  # type: ignore[arg-type]
        tables=_FakeTables(table),  # type: ignore[arg-type]
        tenant_context=FakeTenantContext(),
        event_bus=bus,  # type: ignore[arg-type]
    )
    return uc, bus


def _readies(bus: _SpyBus) -> list[DomainEvent]:
    return [e for e in bus.published if e.type == "order.ready"]


async def test_order_ready_only_when_all_items_ready() -> None:
    i1, i2 = _item("Milanesa"), _item("Ensalada")
    order = _sent_order(i1, i2)
    uc, bus = _advance_item_uc(order, Table(id="tb1", tenant_id="t1", number=7))

    # Primer ítem listo: la orden NO está READY todavía -> no se emite.
    await uc.execute(tenant_id="t1", order_id=order.id, item_id=i1.id, action="preparing")
    await uc.execute(tenant_id="t1", order_id=order.id, item_id=i1.id, action="ready")
    assert _readies(bus) == []

    # Último ítem listo: la orden queda READY -> se emite exactamente uno.
    await uc.execute(tenant_id="t1", order_id=order.id, item_id=i2.id, action="preparing")
    await uc.execute(tenant_id="t1", order_id=order.id, item_id=i2.id, action="ready")

    readies = _readies(bus)
    assert len(readies) == 1
    assert readies[0].tenant_id == "t1"
    assert readies[0].payload == {
        "order_id": order.id,
        "table_id": "tb1",
        "table_number": "7",
        "waiter_id": "w1",
    }


async def test_single_item_order_emits_once() -> None:
    i1 = _item()
    order = _sent_order(i1)
    uc, bus = _advance_item_uc(order, Table(id="tb1", tenant_id="t1", number=3))

    await uc.execute(tenant_id="t1", order_id=order.id, item_id=i1.id, action="preparing")
    await uc.execute(tenant_id="t1", order_id=order.id, item_id=i1.id, action="ready")

    assert len(_readies(bus)) == 1
    assert _readies(bus)[0].payload["table_number"] == "3"


async def test_missing_table_emits_with_empty_number() -> None:
    i1 = _item()
    order = _sent_order(i1)
    uc, bus = _advance_item_uc(order, None)

    await uc.execute(tenant_id="t1", order_id=order.id, item_id=i1.id, action="preparing")
    await uc.execute(tenant_id="t1", order_id=order.id, item_id=i1.id, action="ready")

    assert _readies(bus)[0].payload["table_number"] == ""


async def test_advance_order_ready_emits() -> None:
    order = _sent_order(_item(), _item("Ensalada"))
    bus = _SpyBus()
    uc = AdvanceOrder(
        orders=_FakeOrders(order),  # type: ignore[arg-type]
        tables=_FakeTables(Table(id="tb1", tenant_id="t1", number=9)),  # type: ignore[arg-type]
        tenant_context=FakeTenantContext(),
        event_bus=bus,  # type: ignore[arg-type]
    )

    await uc.execute(tenant_id="t1", order_id=order.id, action="preparing")
    await uc.execute(tenant_id="t1", order_id=order.id, action="ready")

    assert len(_readies(bus)) == 1
    assert _readies(bus)[0].payload["table_number"] == "9"
