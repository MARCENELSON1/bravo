from __future__ import annotations

from uuid import uuid4

from app.application.order.dtos import BatchOrderItemInput, CreateOrderResult
from app.domain.identity.ports import TenantContext
from app.domain.order.entities import Order, OrderItem
from app.domain.order.exceptions import InvalidOrderTransition, OrderNotFound
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import OrderStatus
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
            )
        )
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
                )
            )
            seen.add(new_id)
        if send and order.status is OrderStatus.OPEN:
            order.send_to_kitchen()
        await self._orders.save(order)
        await self._event_bus.publish(_floor_changed(order))
        if send and order.status is OrderStatus.SENT:
            await self._event_bus.publish(_kds_changed(order))
        return order


def _kds_changed(order: Order) -> DomainEvent:
    """A 'refetch the KDS board' signal — carries no data, just ids/status."""
    return DomainEvent(
        type="kds.changed",
        tenant_id=order.tenant_id,
        payload={"order_id": order.id, "status": order.status.value},
    )


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
        order.send_to_kitchen()
        await self._orders.save(order)
        await self._event_bus.publish(_kds_changed(order))
        await self._event_bus.publish(_floor_changed(order))
        return order


class AdvanceOrder:
    """Advance an order's lifecycle (preparing/ready/served/cancel)."""

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
            order.mark_ready()
        elif action == "served":
            order.mark_served()
        elif action == "cancel":
            order.cancel()
        else:
            raise InvalidOrderTransition()
        await self._orders.save(order)
        await self._event_bus.publish(_kds_changed(order))
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

    async def execute(self, *, tenant_id: str) -> list[Order]:
        self._tenant_context.set(tenant_id)
        return await self._orders.list_kds(tenant_id)
