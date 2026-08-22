from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.table_session.sectors import (
    CreateSector,
    DeleteSector,
    ListSectors,
    UpdateSector,
)
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.table_session.entities import Sector
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.sectors import SectorRequest, SectorResponse

router = APIRouter(prefix="/sectors", tags=["sectors"])

_MANAGE = (Role.OWNER, Role.MANAGER)


def _sector_response(s: Sector) -> SectorResponse:
    return SectorResponse(id=s.id, name=s.name, color=s.color, sort_order=s.sort_order)


@router.get("", response_model=list[SectorResponse])
@inject
async def list_sectors(
    identity: AccessClaims = Depends(current_identity),
    use_case: ListSectors = Depends(Provide[Container.list_sectors]),
) -> list[SectorResponse]:
    sectors = await use_case.execute(tenant_id=identity.tenant_id)
    return [_sector_response(s) for s in sectors]


@router.post("", response_model=SectorResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_sector(
    body: SectorRequest,
    identity: AccessClaims = Depends(require_roles(*_MANAGE)),
    use_case: CreateSector = Depends(Provide[Container.create_sector]),
) -> SectorResponse:
    sector = await use_case.execute(
        tenant_id=identity.tenant_id,
        name=body.name,
        color=body.color,
        sort_order=body.sort_order,
    )
    return _sector_response(sector)


@router.put("/{sector_id}", response_model=SectorResponse)
@inject
async def update_sector(
    sector_id: str,
    body: SectorRequest,
    identity: AccessClaims = Depends(require_roles(*_MANAGE)),
    use_case: UpdateSector = Depends(Provide[Container.update_sector]),
) -> SectorResponse:
    sector = await use_case.execute(
        tenant_id=identity.tenant_id,
        sector_id=sector_id,
        name=body.name,
        color=body.color,
        sort_order=body.sort_order,
    )
    return _sector_response(sector)


@router.delete("/{sector_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_sector(
    sector_id: str,
    identity: AccessClaims = Depends(require_roles(*_MANAGE)),
    use_case: DeleteSector = Depends(Provide[Container.delete_sector]),
) -> None:
    await use_case.execute(tenant_id=identity.tenant_id, sector_id=sector_id)
