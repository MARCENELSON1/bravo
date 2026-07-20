from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.identity.accept_invitation import AcceptInvitation
from app.application.identity.dtos import InviteUserInput
from app.application.identity.invite_user import InviteUser
from app.application.identity.set_hourly_rate import SetUserHourlyRate
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.auth import MessageResponse
from app.presentation.schemas.users import (
    AcceptInvitationRequest,
    HourlyRateResponse,
    InviteRequest,
    SetHourlyRateRequest,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/invite", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@inject
async def invite(
    body: InviteRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: InviteUser = Depends(Provide[Container.invite_user]),
) -> MessageResponse:
    await use_case.execute(
        tenant_id=identity.tenant_id,
        invited_by=identity.user_id,
        inviter_role=identity.role,
        data=InviteUserInput(email=body.email, role=body.role),
    )
    return MessageResponse(message="Invitación enviada.")


@router.put("/{user_id}/hourly-rate", response_model=HourlyRateResponse)
@inject
async def set_hourly_rate(
    user_id: str,
    body: SetHourlyRateRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: SetUserHourlyRate = Depends(Provide[Container.set_user_hourly_rate]),
) -> HourlyRateResponse:
    user = await use_case.execute(
        tenant_id=identity.tenant_id,
        user_id=user_id,
        hourly_rate_amount=body.hourly_rate_amount,
    )
    return HourlyRateResponse(user_id=user.id, hourly_rate_amount=user.hourly_rate_amount)


@router.post("/accept-invitation", response_model=MessageResponse)
@inject
async def accept_invitation(
    body: AcceptInvitationRequest,
    use_case: AcceptInvitation = Depends(Provide[Container.accept_invitation]),
) -> MessageResponse:
    await use_case.execute(token=body.token, password=body.password)
    return MessageResponse(message="Invitación aceptada. Ya podés iniciar sesión.")
