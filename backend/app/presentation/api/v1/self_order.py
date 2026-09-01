"""Self-order (Carta QR autopedido) settings — OWNER/MANAGER. Prende el autopedido
y el gate de confirmación del mozo. El pedido del comensal entra por el router
público (`public_menu`); esto es la config del lado dueño."""

from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.application.order.self_order import (
    GetSelfOrderSettings,
    UpdateSelfOrderSettings,
)
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.self_order import (
    SelfOrderSettingsResponse,
    UpdateSelfOrderSettingsRequest,
)

router = APIRouter(prefix="/self-order", tags=["self-order"])


@router.get("/settings", response_model=SelfOrderSettingsResponse)
@inject
async def get_self_order_settings(
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetSelfOrderSettings = Depends(Provide[Container.get_self_order_settings]),
) -> SelfOrderSettingsResponse:
    settings = await use_case.execute(tenant_id=identity.tenant_id)
    return SelfOrderSettingsResponse(
        enabled=settings.enabled, requires_confirmation=settings.requires_confirmation
    )


@router.put("/settings", response_model=SelfOrderSettingsResponse)
@inject
async def update_self_order_settings(
    body: UpdateSelfOrderSettingsRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: UpdateSelfOrderSettings = Depends(Provide[Container.update_self_order_settings]),
) -> SelfOrderSettingsResponse:
    settings = await use_case.execute(
        tenant_id=identity.tenant_id,
        enabled=body.enabled,
        requires_confirmation=body.requires_confirmation,
    )
    return SelfOrderSettingsResponse(
        enabled=settings.enabled, requires_confirmation=settings.requires_confirmation
    )
