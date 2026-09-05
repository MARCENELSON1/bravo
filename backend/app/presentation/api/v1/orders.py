from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.customer.use_cases import AssignOrderCustomer
from app.application.order.dtos import BatchOrderItemInput
from app.application.order.use_cases import (
    AddOrderItem,
    AddOrderItemsBatch,
    AdvanceCourse,
    AdvanceItem,
    AdvanceOrder,
    CloseSettledOrder,
    CreateOrder,
    FireAllCourses,
    FireNextCourse,
    GetOrder,
    ListOrders,
    ListPendingQrOrders,
    MergeOrders,
    RemoveOrderItem,
    ReopenOrder,
    SendOrder,
    SetItemCourse,
    SetItemNote,
    SetItemQuantity,
    TransferOrder,
)
from app.application.table_session.use_cases import AssignTableWaiter
from app.application.tax.quote_order_tax import QuoteOrderTax
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.order.entities import Order
from app.domain.order.value_objects import Course, Station
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.customers import AssignCustomerRequest
from app.presentation.schemas.orders import (
    AddOrderItemRequest,
    AddOrderItemsBatchRequest,
    AssignWaiterRequest,
    CreateOrderRequest,
    CreateOrderResponse,
    MergeOrdersRequest,
    OrderItemResponse,
    OrderResponse,
    SelectedOptionResponse,
    SetItemCourseRequest,
    SetItemNoteRequest,
    SetItemQuantityRequest,
    TaxQuoteResponse,
    TransferOrderRequest,
)

router = APIRouter(prefix="/orders", tags=["orders"])

_FLOOR_ROLES = (Role.WAITER, Role.MANAGER, Role.OWNER)
_KITCHEN_ROLES = (Role.KITCHEN, Role.BAR, Role.MANAGER, Role.OWNER)
_MANAGER_ROLES = (Role.MANAGER, Role.OWNER)
_CASHIER_ROLES = (Role.CASHIER, Role.MANAGER, Role.OWNER)
# Cursos: los bumpea la cocina/barra (KDS) y también el mozo ("servido").
_KDS_OR_FLOOR_ROLES = (Role.KITCHEN, Role.BAR, Role.WAITER, Role.MANAGER, Role.OWNER)
_ITEM_ACTIONS = ("preparing", "ready", "served", "recall")


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
                status=item.status.value,
                station=item.station.value,
                course=item.course.value,
                sent_at=item.sent_at.isoformat() if item.sent_at else None,
                selected_options=[
                    SelectedOptionResponse(
                        option_id=o.option_id, name=o.name, price_delta=o.price_delta
                    )
                    for o in item.selected_options
                ],
            )
            for item in order.items
        ],
        total_amount=order.total().amount,
        active_course=(ac.value if (ac := order.active_course()) else None),
        next_course=(nc.value if (nc := order.next_held_course()) else None),
        source=order.source.value,
        created_at=order.created_at.isoformat() if order.created_at else None,
        customer_id=order.customer_id,
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


@router.get("/pending-qr", response_model=list[OrderResponse])
@inject
async def list_pending_qr_orders(
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: ListPendingQrOrders = Depends(Provide[Container.list_pending_qr]),
) -> list[OrderResponse]:
    """Bandeja "QR por confirmar": pedidos que el comensal hizo por QR y siguen
    OPEN (sin marchar). Un mozo confirma uno con ``POST /orders/{id}/send``."""
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


@router.get("/{order_id}/tax-quote", response_model=TaxQuoteResponse)
@inject
async def tax_quote(
    order_id: str,
    identity: AccessClaims = Depends(current_identity),
    use_case: QuoteOrderTax = Depends(Provide[Container.quote_order_tax]),
) -> TaxQuoteResponse:
    """Sales tax to add on this order for the tenant's regime (read-only).
    AR/IVA → 0 (included); US/TaxJar → the rate by the tenant's fiscal address."""
    quote = await use_case.execute(tenant_id=identity.tenant_id, order_id=order_id)
    return TaxQuoteResponse(
        subtotal_amount=quote.subtotal.amount,
        tax_amount=quote.tax.amount,
        total_amount=quote.total.amount,
        currency=quote.total.currency,
        rate_bps=quote.rate_bps,
        jurisdiction=quote.jurisdiction,
    )


@router.put("/{order_id}/customer", response_model=OrderResponse)
@inject
async def assign_customer(
    order_id: str,
    body: AssignCustomerRequest,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: AssignOrderCustomer = Depends(Provide[Container.assign_order_customer]),
) -> OrderResponse:
    """Atribuir (o desatribuir con customer_id=null) el cliente de la comanda,
    para que se acumule su historial de compras."""
    order = await use_case.execute(
        tenant_id=identity.tenant_id, order_id=order_id, customer_id=body.customer_id
    )
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
        option_ids=body.option_ids,
        course=Course(body.course) if body.course else None,
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


@router.delete("/{order_id}/items/{item_id}", response_model=OrderResponse)
@inject
async def remove_item(
    order_id: str,
    item_id: str,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: RemoveOrderItem = Depends(Provide[Container.remove_order_item]),
) -> OrderResponse:
    order = await use_case.execute(
        tenant_id=identity.tenant_id, order_id=order_id, item_id=item_id
    )
    return order_to_response(order)


@router.patch("/{order_id}/items/{item_id}", response_model=OrderResponse)
@inject
async def set_item_quantity(
    order_id: str,
    item_id: str,
    body: SetItemQuantityRequest,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: SetItemQuantity = Depends(Provide[Container.set_item_quantity]),
) -> OrderResponse:
    order = await use_case.execute(
        tenant_id=identity.tenant_id,
        order_id=order_id,
        item_id=item_id,
        quantity=body.quantity,
    )
    return order_to_response(order)


@router.patch("/{order_id}/items/{item_id}/note", response_model=OrderResponse)
@inject
async def set_item_note(
    order_id: str,
    item_id: str,
    body: SetItemNoteRequest,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: SetItemNote = Depends(Provide[Container.set_item_note]),
) -> OrderResponse:
    """How the dish is wanted (kitchen note) — only while the line is PENDING."""
    note = (body.note or "").strip() or None
    order = await use_case.execute(
        tenant_id=identity.tenant_id, order_id=order_id, item_id=item_id, note=note
    )
    return order_to_response(order)


@router.post("/{order_id}/items/{item_id}/{action}", response_model=OrderResponse)
@inject
async def advance_item(
    order_id: str,
    item_id: str,
    action: str,
    identity: AccessClaims = Depends(require_roles(*_KITCHEN_ROLES)),
    use_case: AdvanceItem = Depends(Provide[Container.advance_item]),
) -> OrderResponse:
    """Bump (or recall) a single item: preparing/ready/served/recall."""
    order = await use_case.execute(
        tenant_id=identity.tenant_id,
        order_id=order_id,
        item_id=item_id,
        action=action,
    )
    return order_to_response(order)


@router.post("/{order_id}/send", response_model=OrderResponse)
@inject
async def send_order(
    order_id: str,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: SendOrder = Depends(Provide[Container.send_order]),
) -> OrderResponse:
    # Confirmar = marchar + quedar dueño de la mesa huérfana (el que confirma).
    order = await use_case.execute(
        tenant_id=identity.tenant_id, order_id=order_id, waiter_id=identity.user_id
    )
    return order_to_response(order)


@router.post("/{order_id}/claim", response_model=OrderResponse)
@inject
async def claim_order(
    order_id: str,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    get_use_case: GetOrder = Depends(Provide[Container.get_order]),
    assign: AssignTableWaiter = Depends(Provide[Container.assign_table_waiter]),
) -> OrderResponse:
    """Tomar una mesa huérfana: el mozo que llama queda dueño (409 si ya tiene
    dueño). Para mesas de autopedido QR que nadie confirmó todavía."""
    order = await get_use_case.execute(tenant_id=identity.tenant_id, order_id=order_id)
    if order.session_id:
        await assign.execute(
            tenant_id=identity.tenant_id,
            session_id=order.session_id,
            waiter_id=identity.user_id,
            only_if_unassigned=True,
            conflict_raises=True,
        )
        order = await get_use_case.execute(
            tenant_id=identity.tenant_id, order_id=order_id
        )
    return order_to_response(order)


@router.post("/{order_id}/assign-waiter", response_model=OrderResponse)
@inject
async def assign_order_waiter(
    order_id: str,
    body: AssignWaiterRequest,
    identity: AccessClaims = Depends(require_roles(*_MANAGER_ROLES)),
    get_use_case: GetOrder = Depends(Provide[Container.get_order]),
    assign: AssignTableWaiter = Depends(Provide[Container.assign_table_waiter]),
) -> OrderResponse:
    """Reasignar el mozo dueño de la mesa (encargado): pisa el dueño actual."""
    order = await get_use_case.execute(tenant_id=identity.tenant_id, order_id=order_id)
    if order.session_id:
        await assign.execute(
            tenant_id=identity.tenant_id,
            session_id=order.session_id,
            waiter_id=body.waiter_id,
        )
        order = await get_use_case.execute(
            tenant_id=identity.tenant_id, order_id=order_id
        )
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


@router.post("/{order_id}/fire-next", response_model=OrderResponse)
@inject
async def fire_next_course(
    order_id: str,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: FireNextCourse = Depends(Provide[Container.fire_next_course]),
) -> OrderResponse:
    """"Marchar principales": el curso en espera más bajo pasa al fuego."""
    order = await use_case.execute(tenant_id=identity.tenant_id, order_id=order_id)
    return order_to_response(order)


@router.post("/{order_id}/fire-all", response_model=OrderResponse)
@inject
async def fire_all_courses(
    order_id: str,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: FireAllCourses = Depends(Provide[Container.fire_all_courses]),
) -> OrderResponse:
    """"Marchar todo": pendientes y en espera al fuego (la mesa quiere todo junto)."""
    order = await use_case.execute(tenant_id=identity.tenant_id, order_id=order_id)
    return order_to_response(order)


@router.post("/{order_id}/courses/{course}/{action}", response_model=OrderResponse)
@inject
async def advance_course(
    order_id: str,
    course: str,
    action: str,
    station: str | None = None,
    identity: AccessClaims = Depends(require_roles(*_KDS_OR_FLOOR_ROLES)),
    use_case: AdvanceCourse = Depends(Provide[Container.advance_course]),
) -> OrderResponse:
    """Un curso entero de una: el "Listo" del KDS por curso (también
    `preparing` / `served`). `station` acota a una estación."""
    order = await use_case.execute(
        tenant_id=identity.tenant_id,
        order_id=order_id,
        course=Course(course),
        action=action,
        station=Station(station) if station else None,
    )
    return order_to_response(order)


@router.patch("/{order_id}/items/{item_id}/course", response_model=OrderResponse)
@inject
async def set_item_course(
    order_id: str,
    item_id: str,
    body: SetItemCourseRequest,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: SetItemCourse = Depends(Provide[Container.set_item_course]),
) -> OrderResponse:
    """Override del curso de una línea ("la provoleta como principal")."""
    order = await use_case.execute(
        tenant_id=identity.tenant_id,
        order_id=order_id,
        item_id=item_id,
        course=Course(body.course),
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


@router.post("/{order_id}/transfer", response_model=OrderResponse)
@inject
async def transfer_order(
    order_id: str,
    body: TransferOrderRequest,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: TransferOrder = Depends(Provide[Container.transfer_order]),
) -> OrderResponse:
    order = await use_case.execute(
        tenant_id=identity.tenant_id, order_id=order_id, table_id=body.table_id
    )
    return order_to_response(order)


@router.post("/{order_id}/free", response_model=OrderResponse)
@inject
async def free_order(
    order_id: str,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: CloseSettledOrder = Depends(Provide[Container.close_settled_order]),
) -> OrderResponse:
    """Liberar la mesa de una comanda ya paga (Autoservicio: el comensal pagó al
    entrar). La marca PAGADA para que se libere del plano; 409 si todavía tiene saldo."""
    order = await use_case.execute(tenant_id=identity.tenant_id, order_id=order_id)
    return order_to_response(order)


@router.post("/{order_id}/reopen", response_model=OrderResponse)
@inject
async def reopen_order(
    order_id: str,
    identity: AccessClaims = Depends(require_roles(*_CASHIER_ROLES)),
    use_case: ReopenOrder = Depends(Provide[Container.reopen_order]),
) -> OrderResponse:
    """Reabrir una comanda ya pagada (revierte venta/stock; bloquea si hay CAE)."""
    order = await use_case.execute(tenant_id=identity.tenant_id, order_id=order_id)
    return order_to_response(order)


@router.post("/{order_id}/merge", response_model=OrderResponse)
@inject
async def merge_orders(
    order_id: str,
    body: MergeOrdersRequest,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: MergeOrders = Depends(Provide[Container.merge_orders]),
) -> OrderResponse:
    """Absorb ``source_order_id`` into this order (this one is the destination)."""
    order = await use_case.execute(
        tenant_id=identity.tenant_id,
        destination_order_id=order_id,
        source_order_id=body.source_order_id,
    )
    return order_to_response(order)
