"""Panel de plataforma (super-admin): gestión del catálogo global de planes.
Todo gateado con ``require_platform_admin`` (flag en el usuario, leído de la DB)."""

from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.billing.platform_use_cases import (
    DeletePlan,
    ListAllPlans,
    SavePlan,
)
from app.container import Container
from app.domain.billing.entities import Plan
from app.domain.billing.features import FEATURE_CATALOG
from app.domain.identity.tokens import AccessClaims
from app.presentation.rbac import require_platform_admin
from app.presentation.schemas.platform import (
    FeatureResponse,
    PlatformPlanRequest,
    PlatformPlanResponse,
)

router = APIRouter(prefix="/platform", tags=["platform"])


def _to_response(plan: Plan) -> PlatformPlanResponse:
    return PlatformPlanResponse(
        id=plan.id,
        tier=plan.tier.value,
        region=plan.region.value,
        amount=plan.price.amount,
        currency=plan.price.currency,
        interval=plan.interval.value,
        features=sorted(plan.features),
        active=plan.active,
    )


@router.get("/features", response_model=list[FeatureResponse])
async def get_features(
    _: AccessClaims = Depends(require_platform_admin),
) -> list[FeatureResponse]:
    return [FeatureResponse(key=k, label=v) for k, v in FEATURE_CATALOG.items()]


@router.get("/plans", response_model=list[PlatformPlanResponse])
@inject
async def list_all_plans(
    _: AccessClaims = Depends(require_platform_admin),
    use_case: ListAllPlans = Depends(Provide[Container.list_all_plans]),
) -> list[PlatformPlanResponse]:
    return [_to_response(p) for p in await use_case.execute()]


@router.post("/plans", response_model=PlatformPlanResponse)
@inject
async def save_plan(
    body: PlatformPlanRequest,
    _: AccessClaims = Depends(require_platform_admin),
    use_case: SavePlan = Depends(Provide[Container.save_plan]),
) -> PlatformPlanResponse:
    plan = await use_case.execute(
        id=body.id,
        tier=body.tier,
        region=body.region,
        amount=body.amount,
        currency=body.currency,
        interval=body.interval,
        features=body.features,
        active=body.active,
    )
    return _to_response(plan)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_plan(
    plan_id: str,
    _: AccessClaims = Depends(require_platform_admin),
    use_case: DeletePlan = Depends(Provide[Container.delete_plan]),
) -> None:
    await use_case.execute(plan_id=plan_id)
