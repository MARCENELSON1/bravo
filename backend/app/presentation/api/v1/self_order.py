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
from app.domain.order.settings import SelfOrderMode, SelfOrderSettings
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.self_order import (
    SelfOrderSettingsResponse,
    UpdateSelfOrderSettingsRequest,
)

router = APIRouter(prefix="/self-order", tags=["self-order"])


def _to_response(settings: SelfOrderSettings) -> SelfOrderSettingsResponse:
    return SelfOrderSettingsResponse(
        enabled=settings.enabled,
        requires_confirmation=settings.requires_confirmation,
        prepay_required=settings.prepay_required,
        mode=settings.mode.value,
    )


@router.get("/settings", response_model=SelfOrderSettingsResponse)
@inject
async def get_self_order_settings(
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetSelfOrderSettings = Depends(Provide[Container.get_self_order_settings]),
) -> SelfOrderSettingsResponse:
    settings = await use_case.execute(tenant_id=identity.tenant_id)
    return _to_response(settings)


@router.put("/settings", response_model=SelfOrderSettingsResponse)
@inject
async def update_self_order_settings(
    body: UpdateSelfOrderSettingsRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: UpdateSelfOrderSettings = Depends(Provide[Container.update_self_order_settings]),
) -> SelfOrderSettingsResponse:
    mode = SelfOrderMode(body.mode) if body.mode is not None else None
    settings = await use_case.execute(
        tenant_id=identity.tenant_id,
        mode=mode,
        enabled=body.enabled,
        requires_confirmation=body.requires_confirmation,
    )
    return _to_response(settings)
