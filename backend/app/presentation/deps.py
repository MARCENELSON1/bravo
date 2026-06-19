from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.container import Container
from app.context import set_current_tenant
from app.domain.identity.ports import TokenService
from app.domain.identity.tokens import AccessClaims

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@inject
async def current_identity(
    token: str = Depends(oauth2_scheme),
    tokens: TokenService = Depends(Provide[Container.token_service]),
) -> AccessClaims:
    """Decode the access token, set the request tenant context, return its claims.

    Token errors (``ExpiredToken`` / ``InvalidToken``) propagate to the domain
    error handlers and become 401 responses.
    """
    claims = tokens.decode_access_token(token)
    set_current_tenant(claims.tenant_id)
    return claims
