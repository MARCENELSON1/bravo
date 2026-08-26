"""Endpoints PÚBLICOS (sin auth) que consume la landing wellnod.com. La landing es
un sitio estático anónimo, por eso no puede llamar a /billing/plans (que exige
login). Este expone una proyección de solo lectura del catálogo de planes activos
de una región — la MISMA fuente de verdad que edita el panel /platform, así el
precio de la landing nunca queda hardcodeado ni desincronizado."""

from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from app.application.billing.use_cases import ListPlans
from app.container import Container
from app.domain.billing.value_objects import BillingRegion
from app.presentation.schemas.billing import PublicPlanResponse

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/plans", response_model=list[PublicPlanResponse])
@inject
async def get_public_plans(
    region: BillingRegion = Query(...),
    use_case: ListPlans = Depends(Provide[Container.list_plans]),
) -> list[PublicPlanResponse]:
    plans = await use_case.execute(region=region)
    return [
        PublicPlanResponse(
            tier=p.tier.value,
            amount=p.price.amount,
            currency=p.price.currency,
            interval=p.interval.value,
        )
        for p in plans
    ]
