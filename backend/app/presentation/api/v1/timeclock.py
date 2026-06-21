from __future__ import annotations

from datetime import datetime

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, Query, status

from app.application.timeclock.presence import (
    GetPresenceChallenge,
    PunchWithPresence,
    RegisterPresenceDevice,
)
from app.application.timeclock.use_cases import (
    AdjustShift,
    ClockIn,
    ClockOut,
    GetMyTimeclock,
    ListShifts,
    Punch,
)
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.timeclock.entities import Shift
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.timeclock import (
    AdjustShiftRequest,
    ClockInRequest,
    MyTimeclockResponse,
    PresenceChallengeResponse,
    PresenceDeviceResponse,
    PresencePunchRequest,
    ShiftResponse,
)

router = APIRouter(tags=["timeclock"])

_MANAGE_ROLES = (Role.OWNER, Role.MANAGER)


def shift_to_response(shift: Shift) -> ShiftResponse:
    return ShiftResponse(
        id=shift.id,
        user_id=shift.user_id,
        clock_in_at=shift.clock_in_at,
        clock_out_at=shift.clock_out_at,
        status=shift.status.value,
        source=shift.source.value,
        worked_minutes=shift.worked_minutes,
        note=shift.note,
        adjusted_by=shift.adjusted_by,
    )


@router.post(
    "/timeclock/clock-in",
    response_model=ShiftResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def clock_in(
    body: ClockInRequest,
    identity: AccessClaims = Depends(current_identity),
    use_case: ClockIn = Depends(Provide[Container.clock_in]),
) -> ShiftResponse:
    shift = await use_case.execute(
        tenant_id=identity.tenant_id, user_id=identity.user_id, note=body.note
    )
    return shift_to_response(shift)


@router.post("/timeclock/clock-out", response_model=ShiftResponse)
@inject
async def clock_out(
    identity: AccessClaims = Depends(current_identity),
    use_case: ClockOut = Depends(Provide[Container.clock_out]),
) -> ShiftResponse:
    shift = await use_case.execute(tenant_id=identity.tenant_id, user_id=identity.user_id)
    return shift_to_response(shift)


@router.post("/timeclock/punch", response_model=ShiftResponse)
@inject
async def punch(
    identity: AccessClaims = Depends(current_identity),
    use_case: Punch = Depends(Provide[Container.punch]),
) -> ShiftResponse:
    shift = await use_case.execute(tenant_id=identity.tenant_id, user_id=identity.user_id)
    return shift_to_response(shift)


@router.get("/timeclock/me", response_model=MyTimeclockResponse)
@inject
async def my_timeclock(
    identity: AccessClaims = Depends(current_identity),
    use_case: GetMyTimeclock = Depends(Provide[Container.get_my_timeclock]),
) -> MyTimeclockResponse:
    result = await use_case.execute(tenant_id=identity.tenant_id, user_id=identity.user_id)
    return MyTimeclockResponse(
        open_shift=shift_to_response(result.open_shift) if result.open_shift else None,
        recent=[shift_to_response(s) for s in result.recent],
    )


@router.get("/timeclock/shifts", response_model=list[ShiftResponse])
@inject
async def list_shifts(
    user_id: str | None = None,
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    identity: AccessClaims = Depends(require_roles(*_MANAGE_ROLES)),
    use_case: ListShifts = Depends(Provide[Container.list_shifts]),
) -> list[ShiftResponse]:
    shifts = await use_case.execute(
        tenant_id=identity.tenant_id, user_id=user_id, since=since, until=until
    )
    return [shift_to_response(s) for s in shifts]


@router.patch("/timeclock/shifts/{shift_id}", response_model=ShiftResponse)
@inject
async def adjust_shift(
    shift_id: str,
    body: AdjustShiftRequest,
    identity: AccessClaims = Depends(require_roles(*_MANAGE_ROLES)),
    use_case: AdjustShift = Depends(Provide[Container.adjust_shift]),
) -> ShiftResponse:
    shift = await use_case.execute(
        tenant_id=identity.tenant_id,
        shift_id=shift_id,
        clock_in_at=body.clock_in_at,
        clock_out_at=body.clock_out_at,
        by=identity.user_id,
    )
    return shift_to_response(shift)


# --- Presence layer (Fase 5.5): QR + typeable code ---


@router.post(
    "/timeclock/presence/devices",
    response_model=PresenceDeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def register_presence_device(
    identity: AccessClaims = Depends(require_roles(*_MANAGE_ROLES)),
    use_case: RegisterPresenceDevice = Depends(Provide[Container.register_presence_device]),
) -> PresenceDeviceResponse:
    token = await use_case.execute(tenant_id=identity.tenant_id)
    return PresenceDeviceResponse(device_token=token)


@router.get("/timeclock/presence/current", response_model=PresenceChallengeResponse)
@inject
async def presence_current(
    x_device_token: str = Header(alias="X-Device-Token"),
    use_case: GetPresenceChallenge = Depends(Provide[Container.get_presence_challenge]),
) -> PresenceChallengeResponse:
    challenge = await use_case.execute(device_token=x_device_token)
    return PresenceChallengeResponse(
        qr_payload=challenge.qr_payload,
        code=challenge.code,
        expires_at=challenge.expires_at,
    )


@router.post("/timeclock/presence/punch", response_model=ShiftResponse)
@inject
async def presence_punch(
    body: PresencePunchRequest,
    identity: AccessClaims = Depends(current_identity),
    use_case: PunchWithPresence = Depends(Provide[Container.punch_with_presence]),
) -> ShiftResponse:
    shift = await use_case.execute(
        tenant_id=identity.tenant_id, user_id=identity.user_id, presented=body.presented
    )
    return shift_to_response(shift)
