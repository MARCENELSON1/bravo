from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.identity.dtos import OnboardTenantInput
from app.application.identity.onboard_tenant import OnboardTenant
from app.application.tenant.fiscal import GetTenantFiscalSettings, UpdateTenantFiscalAddress
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.tenant.entities import Tenant
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.tenants import (
    FiscalAddressRequest,
    FiscalSettingsResponse,
    OnboardingRequest,
    OnboardingResponse,
)

router = APIRouter(prefix="/tenants", tags=["tenants"])

_FISCAL_ROLES = (Role.OWNER, Role.MANAGER)


def _fiscal_response(tenant: Tenant) -> FiscalSettingsResponse:
    return FiscalSettingsResponse(
        country=tenant.country,
        currency=tenant.currency,
        tax_regime=tenant.tax_regime.value,
        tax_engine=tenant.tax_engine.value,
        street=tenant.fiscal_street,
        city=tenant.fiscal_city,
        state=tenant.fiscal_state,
        zip=tenant.fiscal_zip,
    )


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
            country=body.country,
        )
    )
    return OnboardingResponse(
        tenant_id=result.tenant_id,
        user_id=result.user_id,
        message="Comercio creado. Te enviamos un email para verificar tu cuenta.",
    )


@router.get("/fiscal-settings", response_model=FiscalSettingsResponse)
@inject
async def get_fiscal_settings(
    identity: AccessClaims = Depends(require_roles(*_FISCAL_ROLES)),
    use_case: GetTenantFiscalSettings = Depends(Provide[Container.get_tenant_fiscal_settings]),
) -> FiscalSettingsResponse:
    """Régimen fiscal + moneda + dirección del local (para el motor de impuestos)."""
    tenant = await use_case.execute(tenant_id=identity.tenant_id)
    return _fiscal_response(tenant)


@router.put("/fiscal-address", response_model=FiscalSettingsResponse)
@inject
async def update_fiscal_address(
    body: FiscalAddressRequest,
    identity: AccessClaims = Depends(require_roles(*_FISCAL_ROLES)),
    use_case: UpdateTenantFiscalAddress = Depends(Provide[Container.update_tenant_fiscal_address]),
) -> FiscalSettingsResponse:
    """Setear la dirección fiscal del local (la usa TaxJar para calcular por zona)."""
    tenant = await use_case.execute(
        tenant_id=identity.tenant_id,
        street=body.street,
        city=body.city,
        state=body.state,
        zip_code=body.zip,
    )
    return _fiscal_response(tenant)
