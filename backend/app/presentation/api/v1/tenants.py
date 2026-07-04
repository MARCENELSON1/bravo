from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.identity.dtos import OnboardTenantInput
from app.application.identity.onboard_tenant import OnboardTenant
from app.container import Container
from app.presentation.schemas.tenants import OnboardingRequest, OnboardingResponse

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post(
    "/onboarding",
    response_model=OnboardingResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def onboarding(
    body: OnboardingRequest,
    use_case: OnboardTenant = Depends(Provide[Container.onboard_tenant]),
) -> OnboardingResponse:
    result = await use_case.execute(
        OnboardTenantInput(
            tenant_name=body.tenant_name,
            tenant_slug=body.tenant_slug,
            owner_email=body.owner_email,
            owner_password=body.owner_password,
            owner_name=body.owner_name,
        )
    )
    return OnboardingResponse(
        tenant_id=result.tenant_id,
        user_id=result.user_id,
        message="Comercio creado. Te enviamos un email para verificar tu cuenta.",
    )
