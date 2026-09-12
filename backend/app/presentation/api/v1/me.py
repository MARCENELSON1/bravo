from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.application.identity.delete_account import DeleteMyAccount, PreviewAccountDeletion
from app.application.identity.get_my_profile import GetMyProfile
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.presentation.deps import current_identity
from app.presentation.schemas.auth import (
    AccountDeletionScopeResponse,
    DeleteAccountRequest,
    MeResponse,
)

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


@router.get("/me/deletion-scope", response_model=AccountDeletionScopeResponse)
@inject
async def deletion_scope(
    identity: AccessClaims = Depends(current_identity),
    use_case: PreviewAccountDeletion = Depends(Provide[Container.preview_account_deletion]),
) -> AccountDeletionScopeResponse:
    """Qué se borraría, sin borrar nada — para que la confirmación diga la verdad."""
    scope = await use_case.execute(tenant_id=identity.tenant_id, user_id=identity.user_id)
    return AccountDeletionScopeResponse(
        deletes_business=scope.deletes_business, tenant_name=scope.tenant_name
    )


@router.delete("/me", response_model=AccountDeletionScopeResponse)
@inject
async def delete_me(
    body: DeleteAccountRequest,
    identity: AccessClaims = Depends(current_identity),
    use_case: DeleteMyAccount = Depends(Provide[Container.delete_my_account]),
) -> AccountDeletionScopeResponse:
    """Borrar la propia cuenta (App Store 5.1.1(v)). Irreversible."""
    scope = await use_case.execute(
        tenant_id=identity.tenant_id, user_id=identity.user_id, password=body.password
    )
    return AccountDeletionScopeResponse(
        deletes_business=scope.deletes_business, tenant_name=scope.tenant_name
    )
