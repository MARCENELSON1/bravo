"""Endpoints del billing del SaaS (Flujo A). Checkout/cancel requieren OWNER;
los webhooks son públicos (la autenticidad viene de la firma, verificada en el
adapter). El riel (Stripe/MercadoPago) lo elige la región del plan — el candado
anti-arbitraje vive en el dominio, no acá."""

from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Request, status

from app.application.billing.use_cases import (
    CancelSubscription,
    GetSubscription,
    HandleBillingWebhook,
    ListPlans,
    StartSubscriptionCheckout,
)
from app.application.identity.get_my_profile import GetMyProfile
from app.config import Settings
from app.container import Container
from app.domain.billing.value_objects import BillingRail, BillingRegion
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.billing import (
    CheckoutRequest,
    CheckoutResponse,
    PlanResponse,
    SubscriptionResponse,
)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans", response_model=list[PlanResponse])
@inject
async def get_plans(
    region: BillingRegion = Query(...),
    identity: AccessClaims = Depends(current_identity),
    use_case: ListPlans = Depends(Provide[Container.list_plans]),
) -> list[PlanResponse]:
    plans = await use_case.execute(region=region)
    return [
        PlanResponse(
            id=p.id,
            tier=p.tier.value,
            region=p.region.value,
            amount=p.price.amount,
            currency=p.price.currency,
            interval=p.interval.value,
            features=sorted(p.features),
        )
        for p in plans
    ]


@router.get("/subscription", response_model=SubscriptionResponse | None)
@inject
async def get_current_subscription(
    identity: AccessClaims = Depends(current_identity),
    use_case: GetSubscription = Depends(Provide[Container.get_subscription]),
) -> SubscriptionResponse | None:
    sub = await use_case.execute(tenant_id=identity.tenant_id)
    if sub is None:
        return None
    return SubscriptionResponse(
        status=sub.status.value,
        plan_id=sub.plan_id,
        region=sub.region.value,
        rail=sub.rail.value,
        grants_access=sub.grants_access(),
        current_period_end=(
            sub.current_period_end.isoformat() if sub.current_period_end else None
        ),
    )


@router.post("/checkout", response_model=CheckoutResponse)
@inject
async def start_checkout(
    body: CheckoutRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER)),
    profile_uc: GetMyProfile = Depends(Provide[Container.get_my_profile]),
    checkout_uc: StartSubscriptionCheckout = Depends(
        Provide[Container.start_subscription_checkout]
    ),
    config: Settings = Depends(Provide[Container.config]),
) -> CheckoutResponse:
    profile = await profile_uc.execute(
        tenant_id=identity.tenant_id, user_id=identity.user_id
    )
    url = await checkout_uc.execute(
        tenant_id=identity.tenant_id,
        plan_id=body.plan_id,
        payer_email=profile.email,
        success_url=config.billing_success_url,
        cancel_url=config.billing_cancel_url,
    )
    return CheckoutResponse(url=url)


@router.delete("/subscription", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def cancel_current_subscription(
    identity: AccessClaims = Depends(require_roles(Role.OWNER)),
    use_case: CancelSubscription = Depends(Provide[Container.cancel_subscription]),
) -> None:
    await use_case.execute(tenant_id=identity.tenant_id)


@router.post("/webhooks/stripe")
@inject
async def stripe_webhook(
    request: Request,
    use_case: HandleBillingWebhook = Depends(Provide[Container.handle_billing_webhook]),
) -> dict[str, str]:
    payload = await request.body()
    await use_case.execute(
        rail=BillingRail.STRIPE, payload=payload, headers=request.headers
    )
    return {"status": "ok"}


@router.post("/webhooks/mercadopago")
@inject
async def mercadopago_webhook(
    request: Request,
    use_case: HandleBillingWebhook = Depends(Provide[Container.handle_billing_webhook]),
) -> dict[str, str]:
    payload = await request.body()
    await use_case.execute(
        rail=BillingRail.MERCADOPAGO, payload=payload, headers=request.headers
    )
    return {"status": "ok"}
