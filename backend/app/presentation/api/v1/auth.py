from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from app.application.identity.authenticate import Authenticate
from app.application.identity.change_password import ChangePassword
from app.application.identity.logout import Logout
from app.application.identity.refresh_token import RefreshAccessToken
from app.application.identity.request_password_reset import RequestPasswordReset
from app.application.identity.reset_password import ResetPassword
from app.application.identity.verify_email import VerifyEmail
from app.config import Settings
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.presentation.deps import current_identity
from app.presentation.schemas.auth import (
    AccessTokenResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, token: str, config: Settings) -> None:
    """Store the refresh token in an HttpOnly cookie scoped to the auth routes."""
    response.set_cookie(
        key=config.refresh_cookie_name,
        value=token,
        max_age=config.refresh_token_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=config.cookie_secure,
        samesite=config.cookie_samesite,
        path=config.cookie_path,
    )


def _clear_refresh_cookie(response: Response, config: Settings) -> None:
    response.delete_cookie(
        key=config.refresh_cookie_name,
        path=config.cookie_path,
        httponly=True,
        secure=config.cookie_secure,
        samesite=config.cookie_samesite,
    )


def _read_refresh_token(
    request: Request,
    body: RefreshRequest | LogoutRequest | None,
    config: Settings,
) -> str:
    """Prefer the HttpOnly cookie; fall back to the body for non-browser clients."""
    from_cookie = request.cookies.get(config.refresh_cookie_name)
    from_body = body.refresh_token if body else None
    return from_cookie or from_body or ""


@router.post("/login", response_model=AccessTokenResponse)
@inject
async def login(
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    use_case: Authenticate = Depends(Provide[Container.authenticate]),
    config: Settings = Depends(Provide[Container.config]),
) -> AccessTokenResponse:
    # OAuth2 password flow: the tenant slug travels in the form's ``client_id``.
    tokens = await use_case.execute(
        tenant_slug=form.client_id or "", email=form.username, password=form.password
    )
    _set_refresh_cookie(response, tokens.refresh_token, config)
    return AccessTokenResponse(access_token=tokens.access_token)


@router.post("/refresh", response_model=AccessTokenResponse)
@inject
async def refresh(
    request: Request,
    response: Response,
    body: RefreshRequest | None = None,
    use_case: RefreshAccessToken = Depends(Provide[Container.refresh_access_token]),
    config: Settings = Depends(Provide[Container.config]),
) -> AccessTokenResponse:
    token = _read_refresh_token(request, body, config)
    tokens = await use_case.execute(refresh_token=token)
    _set_refresh_cookie(response, tokens.refresh_token, config)
    return AccessTokenResponse(access_token=tokens.access_token)


@router.post("/logout", response_model=MessageResponse)
@inject
async def logout(
    request: Request,
    response: Response,
    body: LogoutRequest | None = None,
    use_case: Logout = Depends(Provide[Container.logout]),
    config: Settings = Depends(Provide[Container.config]),
) -> MessageResponse:
    # Idempotent and neutral: revoke the token (if any) and clear the cookie.
    await use_case.execute(refresh_token=_read_refresh_token(request, body, config))
    _clear_refresh_cookie(response, config)
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
