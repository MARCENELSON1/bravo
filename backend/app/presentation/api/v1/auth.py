from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.application.identity.authenticate import Authenticate
from app.application.identity.change_password import ChangePassword
from app.application.identity.logout import Logout
from app.application.identity.refresh_token import RefreshAccessToken
from app.application.identity.request_password_reset import RequestPasswordReset
from app.application.identity.reset_password import ResetPassword
from app.application.identity.verify_email import VerifyEmail
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.presentation.deps import current_identity
from app.presentation.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@inject
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    use_case: Authenticate = Depends(Provide[Container.authenticate]),
) -> TokenResponse:
    # OAuth2 password flow: the tenant slug travels in the form's ``client_id``.
    tokens = await use_case.execute(
        tenant_slug=form.client_id or "", email=form.username, password=form.password
    )
    return TokenResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


@router.post("/refresh", response_model=TokenResponse)
@inject
async def refresh(
    body: RefreshRequest,
    use_case: RefreshAccessToken = Depends(Provide[Container.refresh_access_token]),
) -> TokenResponse:
    tokens = await use_case.execute(refresh_token=body.refresh_token)
    return TokenResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


@router.post("/logout", response_model=MessageResponse)
@inject
async def logout(
    body: LogoutRequest,
    use_case: Logout = Depends(Provide[Container.logout]),
) -> MessageResponse:
    await use_case.execute(refresh_token=body.refresh_token)
    return MessageResponse(message="Sesión cerrada.")


@router.post("/change-password", response_model=MessageResponse)
@inject
async def change_password(
    body: ChangePasswordRequest,
    identity: AccessClaims = Depends(current_identity),
    use_case: ChangePassword = Depends(Provide[Container.change_password]),
) -> MessageResponse:
    await use_case.execute(
        tenant_id=identity.tenant_id,
        user_id=identity.user_id,
        current_password=body.current_password,
        new_password=body.new_password,
    )
    return MessageResponse(message="Tu contraseña fue actualizada.")


@router.post("/forgot-password", response_model=MessageResponse)
@inject
async def forgot_password(
    body: ForgotPasswordRequest,
    use_case: RequestPasswordReset = Depends(Provide[Container.request_password_reset]),
) -> MessageResponse:
    await use_case.execute(tenant_slug=body.tenant_slug, email=body.email)
    return MessageResponse(
        message="Si el email existe, te enviamos las instrucciones para restablecer la contraseña."
    )


@router.post("/reset-password", response_model=MessageResponse)
@inject
async def reset_password(
    body: ResetPasswordRequest,
    use_case: ResetPassword = Depends(Provide[Container.reset_password]),
) -> MessageResponse:
    await use_case.execute(token=body.token, new_password=body.new_password)
    return MessageResponse(message="Tu contraseña fue restablecida.")


@router.post("/verify-email", response_model=MessageResponse)
@inject
async def verify_email(
    body: VerifyEmailRequest,
    use_case: VerifyEmail = Depends(Provide[Container.verify_email]),
) -> MessageResponse:
    await use_case.execute(token=body.token)
    return MessageResponse(message="Tu email fue verificado.")
