from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.order.dtos import BatchOrderItemInput
from app.application.order.use_cases import (
    AddOrderItem,
    AddOrderItemsBatch,
    AdvanceOrder,
    CreateOrder,
    GetOrder,
    ListOrders,
    SendOrder,
)
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.order.entities import Order
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.orders import (
    AddOrderItemRequest,
    AddOrderItemsBatchRequest,
    CreateOrderRequest,
    CreateOrderResponse,
    OrderItemResponse,
    OrderResponse,
)

router = APIRouter(prefix="/orders", tags=["orders"])

_FLOOR_ROLES = (Role.WAITER, Role.MANAGER, Role.OWNER)
_KITCHEN_ROLES = (Role.KITCHEN, Role.MANAGER, Role.OWNER)
_MANAGER_ROLES = (Role.MANAGER, Role.OWNER)


def order_to_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        table_id=order.table_id,
        waiter_id=order.waiter_id,
        status=order.status.value,
        currency=order.currency,
        items=[
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                name=item.name,
                unit_price_amount=item.unit_price.amount,
                quantity=item.quantity,
                note=item.note,
            )
            for item in order.items
        ],
        total_amount=order.total().amount,
    )


@router.post("", response_model=CreateOrderResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_order(
    body: CreateOrderRequest,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: CreateOrder = Depends(Provide[Container.create_order]),
) -> CreateOrderResponse:
    result = await use_case.execute(
        tenant_id=identity.tenant_id,
        waiter_id=identity.user_id,
        table_id=body.table_id,
        order_id=body.id,
    )
    return CreateOrderResponse(order_id=result.order_id)


@router.get("", response_model=list[OrderResponse])
@inject
async def list_orders(
    identity: AccessClaims = Depends(current_identity),
    use_case: ListOrders = Depends(Provide[Container.list_orders]),
) -> list[OrderResponse]:
    orders = await use_case.execute(tenant_id=identity.tenant_id)
    return [order_to_response(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
@inject
async def get_order(
    order_id: str,
    identity: AccessClaims = Depends(current_identity),
    use_case: GetOrder = Depends(Provide[Container.get_order]),
) -> OrderResponse:
    order = await use_case.execute(tenant_id=identity.tenant_id, order_id=order_id)
    return order_to_response(order)


@router.post("/{order_id}/items", response_model=OrderResponse)
@inject
async def add_item(
    order_id: str,
    body: AddOrderItemRequest,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: AddOrderItem = Depends(Provide[Container.add_order_item]),
) -> OrderResponse:
    order = await use_case.execute(
        tenant_id=identity.tenant_id,
        order_id=order_id,
        product_id=body.product_id,
        quantity=body.quantity,
        note=body.note,
        item_id=body.id,
    )
    return order_to_response(order)


@router.post("/{order_id}/items/batch", response_model=OrderResponse)
@inject
async def add_items_batch(
    order_id: str,
    body: AddOrderItemsBatchRequest,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: AddOrderItemsBatch = Depends(Provide[Container.add_order_items_batch]),
) -> OrderResponse:
    order = await use_case.execute(
        tenant_id=identity.tenant_id,
        order_id=order_id,
        items=[
            BatchOrderItemInput(
                product_id=i.product_id,
                quantity=i.quantity,
                note=i.note,
                item_id=i.id,
            )
            for i in body.items
        ],
        send=body.send,
    )
    return order_to_response(order)


@router.post("/{order_id}/send", response_model=OrderResponse)
@inject
async def send_order(
    order_id: str,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: SendOrder = Depends(Provide[Container.send_order]),
) -> OrderResponse:
    order = await use_case.execute(tenant_id=identity.tenant_id, order_id=order_id)
    return order_to_response(order)


@router.post("/{order_id}/preparing", response_model=OrderResponse)
@inject
async def mark_preparing(
    order_id: str,
    identity: AccessClaims = Depends(require_roles(*_KITCHEN_ROLES)),
    use_case: AdvanceOrder = Depends(Provide[Container.advance_order]),
) -> OrderResponse:
    order = await use_case.execute(
        tenant_id=identity.tenant_id, order_id=order_id, action="preparing"
    )
    return order_to_response(order)


@router.post("/{order_id}/ready", response_model=OrderResponse)
@inject
async def mark_ready(
    order_id: str,
    identity: AccessClaims = Depends(require_roles(*_KITCHEN_ROLES)),
    use_case: AdvanceOrder = Depends(Provide[Container.advance_order]),
) -> OrderResponse:
    order = await use_case.execute(
        tenant_id=identity.tenant_id, order_id=order_id, action="ready"
    )
    return order_to_response(order)


@router.post("/{order_id}/served", response_model=OrderResponse)
@inject
async def mark_served(
    order_id: str,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: AdvanceOrder = Depends(Provide[Container.advance_order]),
) -> OrderResponse:
    order = await use_case.execute(
        tenant_id=identity.tenant_id, order_id=order_id, action="served"
    )
    return order_to_response(order)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
@inject
async def cancel_order(
    order_id: str,
    identity: AccessClaims = Depends(require_roles(*_MANAGER_ROLES)),
    use_case: AdvanceOrder = Depends(Provide[Container.advance_order]),
) -> OrderResponse:
    order = await use_case.execute(
        tenant_id=identity.tenant_id, order_id=order_id, action="cancel"
    )
    return order_to_response(order)
