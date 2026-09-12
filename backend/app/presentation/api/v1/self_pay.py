"""Self-pay (Carta QR — pago desde la mesa) settings — OWNER/MANAGER. Prende el
cobro online del comensal y decide si la pantalla de pago ofrece propina. El pago
del comensal entra por el router público (`public_menu`); esto es la config del
lado dueño."""

from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.application.payment.self_pay import (
    GetSelfPaySettings,
    UpdateSelfPaySettings,
)
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.self_pay import (
    SelfPaySettingsResponse,
    UpdateSelfPaySettingsRequest,
)

router = APIRouter(prefix="/self-pay", tags=["self-pay"])


@router.get("/settings", response_model=SelfPaySettingsResponse)
@inject
async def get_self_pay_settings(
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetSelfPaySettings = Depends(Provide[Container.get_self_pay_settings]),
) -> SelfPaySettingsResponse:
    settings = await use_case.execute(tenant_id=identity.tenant_id)
    return SelfPaySettingsResponse(
        enabled=settings.enabled, tips_enabled=settings.tips_enabled
    )


@router.put("/settings", response_model=SelfPaySettingsResponse)
@inject
async def update_self_pay_settings(
    body: UpdateSelfPaySettingsRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: UpdateSelfPaySettings = Depends(Provide[Container.update_self_pay_settings]),
) -> SelfPaySettingsResponse:
    settings = await use_case.execute(
        tenant_id=identity.tenant_id,
        enabled=body.enabled,
        tips_enabled=body.tips_enabled,
    )
    return SelfPaySettingsResponse(
        enabled=settings.enabled, tips_enabled=settings.tips_enabled
    )
