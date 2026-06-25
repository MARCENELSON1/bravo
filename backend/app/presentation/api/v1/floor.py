from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.application.floor.use_cases import GetFloor
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.presentation.api.v1.orders import order_to_response
from app.presentation.deps import current_identity
from app.presentation.schemas.floor import FloorTableResponse

router = APIRouter(prefix="/floor", tags=["floor"])


@router.get("", response_model=list[FloorTableResponse])
@inject
async def get_floor(
    identity: AccessClaims = Depends(current_identity),
    use_case: GetFloor = Depends(Provide[Container.get_floor]),
) -> list[FloorTableResponse]:
    rows = await use_case.execute(tenant_id=identity.tenant_id)
    return [
        FloorTableResponse(
            id=row.table.id,
            number=row.table.number,
            name=row.table.name,
            status="OCCUPIED" if row.order is not None else "FREE",
            active_order=order_to_response(row.order) if row.order is not None else None,
        )
        for row in rows
    ]
