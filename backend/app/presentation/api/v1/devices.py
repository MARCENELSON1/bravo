"""Registro del push token del device del usuario logueado (Fase 4). Cualquier
user autenticado registra su token; el server lo usa para mandarle avisos
("Mesa lista" / "te asignaron") con la app cerrada."""

from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.notification.use_cases import RegisterDeviceToken
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.presentation.deps import current_identity
from app.presentation.schemas.devices import RegisterDeviceRequest

router = APIRouter(tags=["devices"])


@router.post("/devices", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def register_device(
    body: RegisterDeviceRequest,
    identity: AccessClaims = Depends(current_identity),
    use_case: RegisterDeviceToken = Depends(Provide[Container.register_device_token]),
) -> None:
    await use_case.execute(
        tenant_id=identity.tenant_id,
        user_id=identity.user_id,
        token=body.token,
        platform=body.platform,
    )
