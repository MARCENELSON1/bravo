from __future__ import annotations

from uuid import uuid4

from app.application.clock import utcnow
from app.application.order.dtos import BatchOrderItemInput, CreateOrderResult
from app.domain.identity.ports import TenantContext
from app.domain.order.entities import Order, OrderItem
from app.domain.order.exceptions import InvalidOrderTransition, OrderNotFound
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import ItemStatus, OrderStatus, Station
from app.domain.product.exceptions import InactiveProduct, ProductNotFound
from app.domain.product.repository import ProductRepository
from app.domain.realtime.ports import DomainEvent, EventBus
from app.domain.table.exceptions import TableNotFound
from app.domain.table.repository import TableRepository
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.tenant.repository import TenantRepository


class CreateOrder:
    """Open an order for a table, priced in the tenant's currency."""

    def __init__(
        self,
        orders: OrderRepository,
        tables: TableRepository,
        tenants: TenantRepository,
        tenant_context: TenantContext,
        event_bus: EventBus,
    ) -> None:
        self._orders = orders
        self._tables = tables
        self._tenants = tenants
        self._tenant_context = tenant_context
        self._event_bus = event_bus

    async def execute(
        self,
        *,
        tenant_id: str,
        waiter_id: str,
        table_id: str,
        order_id: str | None = None,
    ) -> CreateOrderResult:
        self._tenant_context.set(tenant_id)
        if order_id is not None:
            existing = await self._orders.get_by_id(tenant_id, order_id)
            if existing is not None:
                return CreateOrderResult(order_id=existing.id)  # idempotent no-op
        if await self._tables.get_by_id(tenant_id, table_id) is None:
            raise TableNotFound()
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFound()
        order = Order(
            id=order_id or str(uuid4()),
            tenant_id=tenant_id,
            table_id=table_id,
            waiter_id=waiter_id,
            currency=tenant.currency,
        )
        await self._orders.add(order)
        await self._event_bus.publish(_floor_changed(order))  # table → occupied
        return CreateOrderResult(order_id=order.id)


class GetOrder:
    def __init__(self, orders: OrderRepository, tenant_context: TenantContext) -> None:
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, order_id: str) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        return order


class AddOrderItem:
    """Add a line item to an OPEN order, snapshotting the product name + price."""

    def __init__(
        self,
        orders: OrderRepository,
        products: ProductRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._orders = orders
        self._products = products
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        order_id: str,
        product_id: str,
        quantity: int,
        note: str | None,
        item_id: str | None = None,
    ) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        if item_id is not None and any(it.id == item_id for it in order.items):
            return order  # idempotent no-op (retry/replay of an item already added)
        product = await self._products.get_by_id(tenant_id, product_id)
        if product is None:
            raise ProductNotFound()
        if not product.active:
            raise InactiveProduct()
        order.add_item(
            OrderItem(
                id=item_id or str(uuid4()),
                product_id=product.id,
                name=product.name,
                unit_price=product.price,
                quantity=quantity,
                note=note,
                station=product.station,
            )
        )
        await self._orders.save(order)
        return order


class RemoveOrderItem:
    """Remove a line item from an order that is still OPEN."""

    def __init__(self, orders: OrderRepository, tenant_context: TenantContext) -> None:
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, order_id: str, item_id: str) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        order.remove_item(item_id)
        await self._orders.save(order)
        return order


class SetItemQuantity:
    """Change a line item's quantity while the order is still OPEN."""

    def __init__(self, orders: OrderRepository, tenant_context: TenantContext) -> None:
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, order_id: str, item_id: str, quantity: int
    ) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        order.set_item_quantity(item_id, quantity)
        await self._orders.save(order)
        return order


class AddOrderItemsBatch:
    """Add several line items (and optionally send) in a single transaction.

    Each line carries an optional client-generated id, so a retry/replay is an
    idempotent no-op. This is what lets the waiter assemble a whole comanda
    (offline if needed) and persist it in one round-trip without duplicating.
    """

    def __init__(
        self,
        orders: OrderRepository,
        products: ProductRepository,
        tenant_context: TenantContext,
        event_bus: EventBus,
    ) -> None:
        self._orders = orders
        self._products = products
        self._tenant_context = tenant_context
        self._event_bus = event_bus

    async def execute(
        self,
        *,
        tenant_id: str,
        order_id: str,
        items: list[BatchOrderItemInput],
        send: bool = False,
    ) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        seen = {it.id for it in order.items}
        for line in items:
            if line.item_id is not None and line.item_id in seen:
                continue  # idempotent no-op for this line
            product = await self._products.get_by_id(tenant_id, line.product_id)
            if product is None:
                raise ProductNotFound()
            if not product.active:
                raise InactiveProduct()
            new_id = line.item_id or str(uuid4())
            order.add_item(
                OrderItem(
                    id=new_id,
                    product_id=product.id,
                    name=product.name,
                    unit_price=product.price,
                    quantity=line.quantity,
                    note=line.note,
                    station=product.station,
                )
            )
            seen.add(new_id)
        marched: list[OrderItem] = []
        # Guard keeps the batch idempotent: a replay (no new PENDING items) must
        # not raise EmptyOrder on the already-marched order.
        if send and any(it.status is ItemStatus.PENDING for it in order.items):
            marched = order.march(utcnow())
        await self._orders.save(order)
        await self._event_bus.publish(_floor_changed(order))
        for event in _kds_changed(order, {it.station for it in marched}):
            await self._event_bus.publish(event)
        return order


def _kds_changed(order: Order, stations: set[Station]) -> list[DomainEvent]:
    """'Refetch the KDS board' signals — one per affected station. Carries no
    data, just ids/station, so tenant isolation never depends on the stream."""
    return [
        DomainEvent(
            type="kds.changed",
            tenant_id=order.tenant_id,
            payload={"order_id": order.id, "station": station.value},
        )
        for station in stations
    ]


def _floor_changed(order: Order) -> DomainEvent:
    """A 'refetch the floor' signal — a table's occupancy/total changed."""
    return DomainEvent(
        type="floor.changed",
        tenant_id=order.tenant_id,
        payload={"table_id": order.table_id},
    )


class SendOrder:
    def __init__(
        self,
        orders: OrderRepository,
        tenant_context: TenantContext,
        event_bus: EventBus,
    ) -> None:
        self._orders = orders
        self._tenant_context = tenant_context
        self._event_bus = event_bus

    async def execute(self, *, tenant_id: str, order_id: str) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        marched = order.march(utcnow())
        await self._orders.save(order)
        for event in _kds_changed(order, {it.station for it in marched}):
            await self._event_bus.publish(event)
        await self._event_bus.publish(_floor_changed(order))
        return order


class AdvanceItem:
    """Bump (or recall) a single item along its kitchen lifecycle. This is what
    the per-station KDS board uses to mark items ready one by one."""

    def __init__(
        self,
        orders: OrderRepository,
        tenant_context: TenantContext,
        event_bus: EventBus,
    ) -> None:
        self._orders = orders
        self._tenant_context = tenant_context
        self._event_bus = event_bus

    async def execute(
        self, *, tenant_id: str, order_id: str, item_id: str, action: str
    ) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        item = order.advance_item(item_id, action, utcnow())
        await self._orders.save(order)
        for event in _kds_changed(order, {item.station}):
            await self._event_bus.publish(event)
        await self._event_bus.publish(_floor_changed(order))
        return order


class AdvanceOrder:
    """Advance a whole order's lifecycle (preparing/ready/served/cancel).

    A convenience that moves every matching item at once; the per-item board uses
    ``AdvanceItem`` instead.
    """

    def __init__(
        self,
        orders: OrderRepository,
        tenant_context: TenantContext,
        event_bus: EventBus,
    ) -> None:
        self._orders = orders
        self._tenant_context = tenant_context
        self._event_bus = event_bus

    async def execute(self, *, tenant_id: str, order_id: str, action: str) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        if action == "preparing":
            order.start_preparing()
        elif action == "ready":
            order.mark_ready(utcnow())
        elif action == "served":
            order.mark_served()
        elif action == "cancel":
            order.cancel()
        else:
            raise InvalidOrderTransition()
        await self._orders.save(order)
        for event in _kds_changed(order, {it.station for it in order.items}):
            await self._event_bus.publish(event)
        await self._event_bus.publish(_floor_changed(order))
        return order


class ListOrders:
    def __init__(self, orders: OrderRepository, tenant_context: TenantContext) -> None:
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, status: OrderStatus | None = None
    ) -> list[Order]:
        self._tenant_context.set(tenant_id)
        return await self._orders.list_by_status(tenant_id, status)


class GetKdsOrders:
    def __init__(self, orders: OrderRepository, tenant_context: TenantContext) -> None:
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, station: Station | None = None
    ) -> list[Order]:
        self._tenant_context.set(tenant_id)
        return await self._orders.list_kds(tenant_id, station)
