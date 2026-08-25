from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.tax.taxjar_connection import (
    ConnectTaxJar,
    DisconnectTaxJar,
    GetTaxJarConnection,
)
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.taxjar import TaxJarConnectionResponse, TaxJarConnectRequest

router = APIRouter(prefix="/integrations/taxjar", tags=["integrations"])

_ADMIN = (Role.OWNER, Role.MANAGER)


@router.put("", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def connect(
    body: TaxJarConnectRequest,
    identity: AccessClaims = Depends(require_roles(*_ADMIN)),
    use_case: ConnectTaxJar = Depends(Provide[Container.connect_taxjar]),
) -> None:
    """Conecta la cuenta de TaxJar del local (su API token). El token se guarda
    cifrado; el reporte/AutoFile se presenta bajo esta cuenta."""
    await use_case.execute(
        tenant_id=identity.tenant_id, api_token=body.api_token, sandbox=body.sandbox
    )


@router.get("", response_model=TaxJarConnectionResponse)
@inject
async def connection_status(
    identity: AccessClaims = Depends(current_identity),
    use_case: GetTaxJarConnection = Depends(Provide[Container.get_taxjar_connection]),
) -> TaxJarConnectionResponse:
    credential = await use_case.execute(tenant_id=identity.tenant_id)
    if credential is None:
        return TaxJarConnectionResponse(connected=False)
    return TaxJarConnectionResponse(connected=True, sandbox=credential.sandbox)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def disconnect(
    identity: AccessClaims = Depends(require_roles(*_ADMIN)),
    use_case: DisconnectTaxJar = Depends(Provide[Container.disconnect_taxjar]),
) -> None:
    await use_case.execute(tenant_id=identity.tenant_id)
