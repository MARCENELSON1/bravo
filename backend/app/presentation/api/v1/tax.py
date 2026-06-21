from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.invoice.connect_afip import (
    ConnectAfip,
    DisconnectAfip,
    GetAfipConnection,
)
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.invoices import AfipConnectionResponse, AfipConnectRequest

router = APIRouter(prefix="/integrations/afip", tags=["integrations"])

_ADMIN = (Role.OWNER, Role.MANAGER)


@router.put("", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def connect(
    body: AfipConnectRequest,
    identity: AccessClaims = Depends(require_roles(*_ADMIN)),
    use_case: ConnectAfip = Depends(Provide[Container.connect_afip]),
) -> None:
    await use_case.execute(
        tenant_id=identity.tenant_id,
        cuit=body.cuit,
        certificate=body.certificate,
        private_key=body.private_key,
        point_of_sale=body.point_of_sale,
        fiscal_condition=body.fiscal_condition.value,
    )


@router.get("", response_model=AfipConnectionResponse)
@inject
async def connection_status(
    identity: AccessClaims = Depends(current_identity),
    use_case: GetAfipConnection = Depends(Provide[Container.get_afip_connection]),
) -> AfipConnectionResponse:
    credential = await use_case.execute(tenant_id=identity.tenant_id)
    if credential is None:
        return AfipConnectionResponse(connected=False)
    return AfipConnectionResponse(
        connected=True,
        cuit=credential.cuit,
        point_of_sale=credential.point_of_sale,
        fiscal_condition=credential.fiscal_condition.value,
        live_mode=credential.live_mode,
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def disconnect(
    identity: AccessClaims = Depends(require_roles(*_ADMIN)),
    use_case: DisconnectAfip = Depends(Provide[Container.disconnect_afip]),
) -> None:
    await use_case.execute(tenant_id=identity.tenant_id)
