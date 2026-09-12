from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.application.floor.dtos import FloorTable
from app.application.floor.use_cases import GetFloor
from app.application.table_session.use_cases import (
    CloseSession,
    OpenSession,
    RequestBill,
    SetSessionPax,
)
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.table_session.entities import TableSession
from app.domain.user.value_objects import Role
from app.presentation.api.v1.orders import order_to_response
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.floor import (
    FloorSessionResponse,
    FloorTableResponse,
    OpenSessionRequest,
    SessionResponse,
    SetSessionPaxRequest,
)

router = APIRouter(prefix="/floor", tags=["floor"])

_FLOOR_ROLES = (Role.WAITER, Role.MANAGER, Role.OWNER, Role.CASHIER)


def _floor_row(row: FloorTable) -> FloorTableResponse:
    session = row.session
    return FloorTableResponse(
        id=row.table.id,
        number=row.table.number,
        name=row.table.name,
        status="OCCUPIED" if row.order is not None else "FREE",
        active_order=order_to_response(row.order) if row.order is not None else None,
        session=(
            FloorSessionResponse(
                id=session.id,
                state=session.status.value,
                state_since=session.state_since,
                pax=session.pax,
                waiter_id=session.waiter_id,
                waiter_name=session.waiter_name,
                sector_id=session.sector_id,
            )
            if session is not None
            else None
        ),
        sector_id=row.table.sector_id,
        capacity=row.table.capacity,
    )


def _session_response(session: TableSession) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        table_id=session.table_id,
        status=session.status.value,
        pax=session.pax,
        waiter_id=session.waiter_id,
    )


@router.get("", response_model=list[FloorTableResponse])
@inject
async def get_floor(
    identity: AccessClaims = Depends(current_identity),
    use_case: GetFloor = Depends(Provide[Container.get_floor]),
) -> list[FloorTableResponse]:
    rows = await use_case.execute(tenant_id=identity.tenant_id)
    return [_floor_row(row) for row in rows]


@router.post("/sessions", response_model=SessionResponse)
@inject
async def open_session(
    body: OpenSessionRequest,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: OpenSession = Depends(Provide[Container.open_session]),
) -> SessionResponse:
    session = await use_case.execute(
        tenant_id=identity.tenant_id,
        table_id=body.table_id,
        pax=body.pax,
        waiter_id=body.waiter_id or identity.user_id,
    )
    return _session_response(session)


@router.post("/sessions/{session_id}/bill", response_model=SessionResponse)
@inject
async def request_bill(
    session_id: str,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: RequestBill = Depends(Provide[Container.request_bill]),
) -> SessionResponse:
    session = await use_case.execute(
        tenant_id=identity.tenant_id, session_id=session_id
    )
    return _session_response(session)


@router.post("/sessions/{session_id}/close", response_model=SessionResponse)
@inject
async def close_session(
    session_id: str,
    identity: AccessClaims = Depends(require_roles(Role.MANAGER, Role.OWNER)),
    use_case: CloseSession = Depends(Provide[Container.close_session]),
) -> SessionResponse:
    """Cerrar la mesa a mano (abierta por error, se fueron sin pedir). Se niega
    si queda una comanda activa: cobrarla o anularla primero."""
    session = await use_case.execute(
        tenant_id=identity.tenant_id, session_id=session_id
    )
    return _session_response(session)


@router.patch("/sessions/{session_id}/pax", response_model=SessionResponse)
@inject
async def set_session_pax(
    session_id: str,
    body: SetSessionPaxRequest,
    identity: AccessClaims = Depends(require_roles(*_FLOOR_ROLES)),
    use_case: SetSessionPax = Depends(Provide[Container.set_session_pax]),
) -> SessionResponse:
    session = await use_case.execute(
        tenant_id=identity.tenant_id, session_id=session_id, pax=body.pax
    )
    return _session_response(session)
