from __future__ import annotations

from fastapi import APIRouter, Depends

from app.domain.identity.tokens import AccessClaims
from app.presentation.deps import current_identity
from app.presentation.schemas.auth import PingResponse

router = APIRouter(tags=["health"])


@router.get("/ping", response_model=PingResponse)
async def ping(identity: AccessClaims = Depends(current_identity)) -> PingResponse:
    """Echo the tenant/user from the access token — demonstrates tenant scoping."""
    return PingResponse(
        tenant_id=identity.tenant_id,
        user_id=identity.user_id,
        role=str(identity.role),
    )
