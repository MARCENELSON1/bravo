from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject

from app.application.identity.get_my_profile import GetMyProfile
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.presentation.deps import current_identity
from app.presentation.schemas.auth import MeResponse

router = APIRouter(tags=["identity"])


@router.get("/me", response_model=MeResponse)
@inject
async def me(
    identity: AccessClaims = Depends(current_identity),
    use_case: GetMyProfile = Depends(Provide[Container.get_my_profile]),
) -> MeResponse:
    """Whoami with human-facing names (user + tenant) — feeds the app shell."""
    profile = await use_case.execute(
        tenant_id=identity.tenant_id, user_id=identity.user_id
    )
    return MeResponse(
        tenant_id=profile.tenant_id,
        user_id=profile.user_id,
        role=profile.role,
        email=profile.email,
        name=profile.name,
        tenant_name=profile.tenant_name,
    )
