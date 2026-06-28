from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.payment.use_cases import (
    ListOrderPayments,
    RefundPayment,
    RegisterPayment,
)
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.payment.entities import Payment
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.payments import PaymentResponse, RegisterPaymentRequest

router = APIRouter(tags=["payments"])

_COBRO_ROLES = (Role.CASHIER, Role.MANAGER, Role.OWNER)


def payment_to_response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        direction=payment.direction.value,
        order_id=payment.order_id,
        method=payment.method.value,
        amount=payment.amount.amount,
        currency=payment.amount.currency,
        status=payment.status.value,
        category=payment.category,
        counterparty=payment.counterparty,
        description=payment.description,
        checkout_url=payment.checkout_url,
    )


@router.post(
    "/orders/{order_id}/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def register_payment(
    order_id: str,
    body: RegisterPaymentRequest,
    identity: AccessClaims = Depends(require_roles(*_COBRO_ROLES)),
    use_case: RegisterPayment = Depends(Provide[Container.register_payment]),
) -> PaymentResponse:
    payment = await use_case.execute(
        tenant_id=identity.tenant_id,
        order_id=order_id,
        method=body.method.value,
        amount=body.amount,
    )
    return payment_to_response(payment)


@router.get("/orders/{order_id}/payments", response_model=list[PaymentResponse])
@inject
async def list_order_payments(
    order_id: str,
    identity: AccessClaims = Depends(current_identity),
    use_case: ListOrderPayments = Depends(Provide[Container.list_order_payments]),
) -> list[PaymentResponse]:
    payments = await use_case.execute(tenant_id=identity.tenant_id, order_id=order_id)
    return [payment_to_response(p) for p in payments]


@router.post("/payments/{payment_id}/refund", response_model=PaymentResponse)
@inject
async def refund_payment(
    payment_id: str,
    identity: AccessClaims = Depends(require_roles(*_COBRO_ROLES)),
    use_case: RefundPayment = Depends(Provide[Container.refund_payment]),
) -> PaymentResponse:
    payment = await use_case.execute(tenant_id=identity.tenant_id, payment_id=payment_id)
    return payment_to_response(payment)
