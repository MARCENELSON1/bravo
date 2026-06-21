"""Payment-provider connections (Fase 3.5): the tenant links its own MercadoPago
account via OAuth. ``/connect`` returns the authorize URL (the SPA redirects to
it); ``/callback`` is public and trusted via the signed ``state``, and redirects
back to the frontend."""

from __future__ import annotations

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse

from app.application.payment.connect_mercadopago import (
    CompleteMercadoPagoConnection,
    DisconnectMercadoPago,
    GetMercadoPagoConnection,
    StartMercadoPagoConnection,
)
from app.config import Settings
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.integrations import ConnectUrlResponse, MpConnectionResponse

router = APIRouter(prefix="/integrations/mercadopago", tags=["integrations"])

_ADMIN = (Role.OWNER, Role.MANAGER)


@router.get("/connect", response_model=ConnectUrlResponse)
@inject
async def connect(
    identity: AccessClaims = Depends(require_roles(*_ADMIN)),
    use_case: StartMercadoPagoConnection = Depends(Provide[Container.start_mp_connection]),
) -> ConnectUrlResponse:
    url = await use_case.execute(tenant_id=identity.tenant_id)
    return ConnectUrlResponse(url=url)


@router.get("/callback")
@inject
async def callback(
    code: Annotated[str, Query()],
    state: Annotated[str, Query()],
    use_case: CompleteMercadoPagoConnection = Depends(Provide[Container.complete_mp_connection]),
    settings: Settings = Depends(Provide[Container.config]),
) -> RedirectResponse:
    target = f"{settings.app_base_url}/app/integrations"
    try:
        await use_case.execute(code=code, state=state)
    except Exception:
        return RedirectResponse(url=f"{target}?mp=error", status_code=302)
    return RedirectResponse(url=f"{target}?mp=ok", status_code=302)


@router.get("", response_model=MpConnectionResponse)
@inject
async def connection_status(
    identity: AccessClaims = Depends(current_identity),
    use_case: GetMercadoPagoConnection = Depends(Provide[Container.get_mp_connection]),
) -> MpConnectionResponse:
    credential = await use_case.execute(tenant_id=identity.tenant_id)
    if credential is None:
        return MpConnectionResponse(connected=False)
    return MpConnectionResponse(
        connected=True,
        nickname=credential.nickname,
        external_account_id=credential.external_account_id,
        live_mode=credential.live_mode,
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def disconnect(
    identity: AccessClaims = Depends(require_roles(*_ADMIN)),
    use_case: DisconnectMercadoPago = Depends(Provide[Container.disconnect_mp]),
) -> None:
    await use_case.execute(tenant_id=identity.tenant_id)
