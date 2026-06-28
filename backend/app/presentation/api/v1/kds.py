from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.application.order.use_cases import GetKdsOrders
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.order.value_objects import Station
from app.domain.user.value_objects import Role
from app.presentation.api.v1.orders import order_to_response
from app.presentation.rbac import require_roles
from app.presentation.schemas.orders import OrderResponse

router = APIRouter(prefix="/kds", tags=["kds"])

_KDS_ROLES = (Role.KITCHEN, Role.BAR, Role.MANAGER, Role.OWNER)


@router.get("/orders", response_model=list[OrderResponse])
@inject
async def kds_orders(
    station: Station | None = None,
    identity: AccessClaims = Depends(require_roles(*_KDS_ROLES)),
    use_case: GetKdsOrders = Depends(Provide[Container.get_kds_orders]),
) -> list[OrderResponse]:
    """Orders with at least one item still being made. Filter by ``?station=``
    (KITCHEN/BAR) to drive the per-station board."""
    orders = await use_case.execute(tenant_id=identity.tenant_id, station=station)
    return [order_to_response(o) for o in orders]
