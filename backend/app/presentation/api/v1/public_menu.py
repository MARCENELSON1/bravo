"""Carta pública (QR de mesa) — endpoint SIN auth. El comensal escanea el QR de su
mesa y ve la carta del local: el token porta el tenant, así que no hace falta login.
Solo lectura y solo lo público (activos, sin costos). Molde: ``public.py``/``leads.py``."""

from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from app.application.order.self_order import CustomerOrderLineInput, SubmitCustomerOrder
from app.application.order.table_bill import GetTableBill
from app.application.payment.pay_table_bill import (
    GetPublicPaymentReceipt,
    GetPublicPaymentStatus,
    PayTableBill,
)
from app.application.public_menu.use_cases import GetPublicMenu, RequestTableAttention
from app.container import Container
from app.domain.order.value_objects import OrderStatus
from app.domain.public_menu.value_objects import TableCallKind
from app.presentation.schemas.public_menu import (
    CustomerOrderRequest,
    CustomerOrderResponse,
    PublicMenuCategoryResponse,
    PublicMenuItemResponse,
    PublicMenuModifierGroupResponse,
    PublicMenuModifierOptionResponse,
    PublicMenuResponse,
    PublicPaymentReceiptResponse,
    PublicPaymentStatusResponse,
    PublicReceiptItemResponse,
    TableBillItemResponse,
    TableBillOptionResponse,
    TableBillResponse,
    TableCallRequest,
    TableCallResponse,
    TablePayRequest,
    TablePayResponse,
)

router = APIRouter(prefix="/public", tags=["public-menu"])


@router.get("/menu", response_model=PublicMenuResponse)
@inject
async def get_public_menu(
    token: str = Query(...),
    use_case: GetPublicMenu = Depends(Provide[Container.get_public_menu]),
) -> PublicMenuResponse:
    menu = await use_case.execute(token=token)
    return PublicMenuResponse(
        tenant_name=menu.tenant_name,
        currency=menu.currency,
        locale=menu.locale,
        self_order_enabled=menu.self_order_enabled,
        self_order_requires_confirmation=menu.self_order_requires_confirmation,
        categories=[
            PublicMenuCategoryResponse(
                name=category.name,
                items=[
                    PublicMenuItemResponse(
                        id=item.id,
                        name=item.name,
                        price_amount=item.price_amount,
                        image_url=item.image_url,
                        description=item.description,
                        available_today=item.available_today,
                        modifier_groups=[
                            PublicMenuModifierGroupResponse(
                                id=group.id,
                                name=group.name,
                                min_select=group.min_select,
                                max_select=group.max_select,
                                required=group.required,
                                options=[
                                    PublicMenuModifierOptionResponse(
                                        id=opt.id, name=opt.name, price_delta=opt.price_delta
                                    )
                                    for opt in group.options
                                ],
                            )
                            for group in item.modifier_groups
                        ],
                    )
                    for item in category.items
                ],
            )
            for category in menu.categories
        ],
    )


@router.get("/table/bill", response_model=TableBillResponse)
@inject
async def get_table_bill(
    token: str = Query(...),
    use_case: GetTableBill = Depends(Provide[Container.get_table_bill]),
) -> TableBillResponse:
    bill = await use_case.execute(token=token)
    return TableBillResponse(
        currency=bill.currency,
        items=[
            TableBillItemResponse(
                name=item.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                selected_options=[
                    TableBillOptionResponse(name=opt.name, price_delta=opt.price_delta)
                    for opt in item.selected_options
                ],
            )
            for item in bill.items
        ],
        total=bill.total,
        paid=bill.paid,
        balance=bill.balance,
        online_pay_available=bill.online_pay_available,
        tips_enabled=bill.tips_enabled,
    )


@router.post("/table/pay", response_model=TablePayResponse)
@inject
async def pay_table_bill(
    body: TablePayRequest,
    use_case: PayTableBill = Depends(Provide[Container.pay_table_bill]),
) -> TablePayResponse:
    result = await use_case.execute(
        token=body.token,
        tip=body.tip,
        amount=body.amount,
        idempotency_key=body.idempotency_key,
    )
    return TablePayResponse(
        payment_id=result.payment_id,
        order_id=result.order_id,
        status=result.status,
        amount=result.amount,
        tip=result.tip,
        checkout_url=result.checkout_url,
    )


@router.get("/table/payment/{payment_id}", response_model=PublicPaymentStatusResponse)
@inject
async def get_table_payment_status(
    payment_id: str,
    token: str = Query(...),
    use_case: GetPublicPaymentStatus = Depends(Provide[Container.get_public_payment_status]),
) -> PublicPaymentStatusResponse:
    payment = await use_case.execute(token=token, payment_id=payment_id)
    return PublicPaymentStatusResponse(
        payment_id=payment.id,
        status=payment.status.value,
        amount=payment.amount.amount,
        tip=payment.tip_amount,
    )


@router.get("/table/receipt/{payment_id}", response_model=PublicPaymentReceiptResponse)
@inject
async def get_table_payment_receipt(
    payment_id: str,
    token: str = Query(...),
    use_case: GetPublicPaymentReceipt = Depends(Provide[Container.get_public_payment_receipt]),
) -> PublicPaymentReceiptResponse:
    receipt = await use_case.execute(token=token, payment_id=payment_id)
    return PublicPaymentReceiptResponse(
        venue_name=receipt.venue_name,
        currency=receipt.currency,
        items=[
            PublicReceiptItemResponse(
                name=item.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                selected_options=[
                    TableBillOptionResponse(name=opt.name, price_delta=opt.price_delta)
                    for opt in item.selected_options
                ],
            )
            for item in receipt.items
        ],
        amount=receipt.amount,
        tip=receipt.tip,
        method=receipt.method,
        paid_at=receipt.paid_at,
    )


@router.post("/table/call-waiter", response_model=TableCallResponse)
@inject
async def call_waiter(
    body: TableCallRequest,
    use_case: RequestTableAttention = Depends(Provide[Container.request_table_attention]),
) -> TableCallResponse:
    await use_case.execute(token=body.token, kind=TableCallKind.WAITER)
    return TableCallResponse()


@router.post("/table/request-bill", response_model=TableCallResponse)
@inject
async def request_bill(
    body: TableCallRequest,
    use_case: RequestTableAttention = Depends(Provide[Container.request_table_attention]),
) -> TableCallResponse:
    await use_case.execute(token=body.token, kind=TableCallKind.BILL)
    return TableCallResponse()


@router.post("/table/order", response_model=CustomerOrderResponse)
@inject
async def submit_customer_order(
    body: CustomerOrderRequest,
    use_case: SubmitCustomerOrder = Depends(Provide[Container.submit_customer_order]),
) -> CustomerOrderResponse:
    order = await use_case.execute(
        token=body.token,
        lines=[
            CustomerOrderLineInput(
                product_id=line.product_id,
                quantity=line.quantity,
                note=line.note,
                option_ids=line.option_ids,
            )
            for line in body.lines
        ],
    )
    # OPEN = ítems PENDING sin marchar → el gate estaba ON (el mozo confirma).
    return CustomerOrderResponse(
        order_id=order.id,
        status=order.status.value,
        requires_confirmation=order.status is OrderStatus.OPEN,
    )
