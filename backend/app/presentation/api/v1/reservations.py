from __future__ import annotations

from datetime import datetime

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status

from app.application.reservation.use_cases import (
    CancelReservation,
    CompleteReservation,
    ConfirmReservation,
    CreateReservation,
    GetReservation,
    ListReservations,
    MarkNoShow,
    SeatReservation,
    UpdateReservation,
)
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.reservation.entities import Reservation
from app.domain.reservation.value_objects import ReservationStatus, ServiceTurn
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.reservations import (
    CreateReservationRequest,
    CreateReservationResponse,
    ReservationResponse,
    UpdateReservationRequest,
)

router = APIRouter(prefix="/reservations", tags=["reservations"])

# Front of house manages reservations.
_FOH = (Role.OWNER, Role.MANAGER, Role.WAITER, Role.CASHIER)


def _reservation_response(r: Reservation) -> ReservationResponse:
    return ReservationResponse(
        id=r.id,
        customer_name=r.customer_name,
        customer_phone=r.customer_phone,
        party_size=r.party_size,
        reserved_at=r.reserved_at,
        turn=r.turn.value,
        table_id=r.table_id,
        status=r.status.value,
        note=r.note,
        created_at=r.created_at,
    )


@router.post(
    "",
    response_model=CreateReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_reservation(
    body: CreateReservationRequest,
    identity: AccessClaims = Depends(require_roles(*_FOH)),
    use_case: CreateReservation = Depends(Provide[Container.create_reservation]),
) -> CreateReservationResponse:
    reservation = await use_case.execute(
        tenant_id=identity.tenant_id,
        customer_name=body.customer_name,
        party_size=body.party_size,
        reserved_at=body.reserved_at,
        turn=body.turn,
        customer_phone=body.customer_phone,
        table_id=body.table_id,
        note=body.note,
    )
    return CreateReservationResponse(reservation_id=reservation.id)


@router.get("", response_model=list[ReservationResponse])
@inject
async def list_reservations(
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    turn: ServiceTurn | None = None,
    status_filter: ReservationStatus | None = Query(default=None, alias="status"),
    table_id: str | None = None,
    identity: AccessClaims = Depends(require_roles(*_FOH)),
    use_case: ListReservations = Depends(Provide[Container.list_reservations]),
) -> list[ReservationResponse]:
    reservations = await use_case.execute(
        tenant_id=identity.tenant_id,
        since=since,
        until=until,
        turn=turn,
        status=status_filter,
        table_id=table_id,
    )
    return [_reservation_response(r) for r in reservations]


@router.get("/{reservation_id}", response_model=ReservationResponse)
@inject
async def get_reservation(
    reservation_id: str,
    identity: AccessClaims = Depends(require_roles(*_FOH)),
    use_case: GetReservation = Depends(Provide[Container.get_reservation]),
) -> ReservationResponse:
    reservation = await use_case.execute(
        tenant_id=identity.tenant_id, reservation_id=reservation_id
    )
    return _reservation_response(reservation)


@router.patch("/{reservation_id}", response_model=ReservationResponse)
@inject
async def update_reservation(
    reservation_id: str,
    body: UpdateReservationRequest,
    identity: AccessClaims = Depends(require_roles(*_FOH)),
    use_case: UpdateReservation = Depends(Provide[Container.update_reservation]),
) -> ReservationResponse:
    reservation = await use_case.execute(
        tenant_id=identity.tenant_id,
        reservation_id=reservation_id,
        reserved_at=body.reserved_at,
        turn=body.turn,
        party_size=body.party_size,
        table_id=body.table_id,
    )
    return _reservation_response(reservation)


@router.post("/{reservation_id}/confirm", response_model=ReservationResponse)
@inject
async def confirm_reservation(
    reservation_id: str,
    identity: AccessClaims = Depends(require_roles(*_FOH)),
    use_case: ConfirmReservation = Depends(Provide[Container.confirm_reservation]),
) -> ReservationResponse:
    return _reservation_response(
        await use_case.execute(tenant_id=identity.tenant_id, reservation_id=reservation_id)
    )


@router.post("/{reservation_id}/seat", response_model=ReservationResponse)
@inject
async def seat_reservation(
    reservation_id: str,
    identity: AccessClaims = Depends(require_roles(*_FOH)),
    use_case: SeatReservation = Depends(Provide[Container.seat_reservation]),
) -> ReservationResponse:
    return _reservation_response(
        await use_case.execute(tenant_id=identity.tenant_id, reservation_id=reservation_id)
    )


@router.post("/{reservation_id}/complete", response_model=ReservationResponse)
@inject
async def complete_reservation(
    reservation_id: str,
    identity: AccessClaims = Depends(require_roles(*_FOH)),
    use_case: CompleteReservation = Depends(Provide[Container.complete_reservation]),
) -> ReservationResponse:
    return _reservation_response(
        await use_case.execute(tenant_id=identity.tenant_id, reservation_id=reservation_id)
    )


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse)
@inject
async def cancel_reservation(
    reservation_id: str,
    identity: AccessClaims = Depends(require_roles(*_FOH)),
    use_case: CancelReservation = Depends(Provide[Container.cancel_reservation]),
) -> ReservationResponse:
    return _reservation_response(
        await use_case.execute(tenant_id=identity.tenant_id, reservation_id=reservation_id)
    )


@router.post("/{reservation_id}/no-show", response_model=ReservationResponse)
@inject
async def no_show_reservation(
    reservation_id: str,
    identity: AccessClaims = Depends(require_roles(*_FOH)),
    use_case: MarkNoShow = Depends(Provide[Container.mark_no_show]),
) -> ReservationResponse:
    return _reservation_response(
        await use_case.execute(tenant_id=identity.tenant_id, reservation_id=reservation_id)
    )
