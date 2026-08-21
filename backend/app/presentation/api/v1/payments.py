from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.payment.fee_rates import GetPaymentFeeRates, UpdatePaymentFeeRates
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
from app.presentation.schemas.payments import (
    FeeRateItem,
    FeeRatesResponse,
    PaymentResponse,
    RegisterPaymentRequest,
    UpdateFeeRatesRequest,
)

router = APIRouter(tags=["payments"])

_COBRO_ROLES = (Role.CASHIER, Role.MANAGER, Role.OWNER)


def payment_to_response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        direction=payment.direction.value,
        order_id=payment.order_id,
        method=payment.method.value,
        amount=payment.amount.amount,
        tip_amount=payment.tip_amount,
        currency=payment.amount.currency,
        status=payment.status.value,
        category=payment.category,
        counterparty=payment.counterparty,
        description=payment.description,
        checkout_url=payment.checkout_url,
    )


def _fee_rates_response(rates: dict[str, int]) -> FeeRatesResponse:
    return FeeRatesResponse(
        rates=[FeeRateItem(method=m, fee_bps=b) for m, b in sorted(rates.items())]
    )


@router.get("/payments/fee-rates", response_model=FeeRatesResponse)
@inject
async def get_fee_rates(
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetPaymentFeeRates = Depends(Provide[Container.get_payment_fee_rates]),
) -> FeeRatesResponse:
    """Comisiones (slice B): tasas por método del tenant (bps)."""
    return _fee_rates_response(await use_case.execute(tenant_id=identity.tenant_id))


@router.put("/payments/fee-rates", response_model=FeeRatesResponse)
@inject
async def update_fee_rates(
    body: UpdateFeeRatesRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: UpdatePaymentFeeRates = Depends(Provide[Container.update_payment_fee_rates]),
) -> FeeRatesResponse:
    """Upsert de tasas por método (solo toca los enviados)."""
    rates = await use_case.execute(
        tenant_id=identity.tenant_id,
        rates={item.method.value: item.fee_bps for item in body.rates},
    )
    return _fee_rates_response(rates)


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
        tip=body.tip,
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
