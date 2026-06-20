from __future__ import annotations

from uuid import uuid4

from app.application.order.dtos import CreateOrderResult
from app.domain.identity.ports import TenantContext
from app.domain.order.entities import Order, OrderItem
from app.domain.order.exceptions import InvalidOrderTransition, OrderNotFound
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import OrderStatus
from app.domain.product.exceptions import InactiveProduct, ProductNotFound
from app.domain.product.repository import ProductRepository
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
    ) -> None:
        self._orders = orders
        self._tables = tables
        self._tenants = tenants
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, waiter_id: str, table_id: str
    ) -> CreateOrderResult:
        self._tenant_context.set(tenant_id)
        if await self._tables.get_by_id(tenant_id, table_id) is None:
            raise TableNotFound()
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFound()
        order = Order(
            id=str(uuid4()),
            tenant_id=tenant_id,
            table_id=table_id,
            waiter_id=waiter_id,
            currency=tenant.currency,
        )
        await self._orders.add(order)
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
    ) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        product = await self._products.get_by_id(tenant_id, product_id)
        if product is None:
            raise ProductNotFound()
        if not product.active:
            raise InactiveProduct()
        order.add_item(
            OrderItem(
                id=str(uuid4()),
                product_id=product.id,
                name=product.name,
                unit_price=product.price,
                quantity=quantity,
            )
        )
        await self._orders.save(order)
        return order


class SendOrder:
    def __init__(self, orders: OrderRepository, tenant_context: TenantContext) -> None:
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, order_id: str) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        order.send_to_kitchen()
        await self._orders.save(order)
        return order


class AdvanceOrder:
    """Advance an order's lifecycle (preparing/ready/served/cancel)."""

    def __init__(self, orders: OrderRepository, tenant_context: TenantContext) -> None:
        self._orders = orders
        self._tenant_context = tenant_context

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
