from __future__ import annotations

from collections.abc import Awaitable, Callable

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.exceptions import InsufficientRole
from app.domain.user.repository import UserRepository
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity


def require_roles(*roles: Role) -> Callable[[AccessClaims], Awaitable[AccessClaims]]:
    """Dependency factory that allows only the given roles (else 403)."""

    async def checker(identity: AccessClaims = Depends(current_identity)) -> AccessClaims:
        if identity.role not in roles:
            raise InsufficientRole()
        return identity

    return checker


@inject
async def require_platform_admin(
    identity: AccessClaims = Depends(current_identity),
    users: UserRepository = Depends(Provide[Container.user_repository]),
) -> AccessClaims:
    """Solo super-admins de plataforma (gestión del catálogo global de planes).
    Lee el flag ``platform_admin`` de la DB, no del token (el token se emite en un
    archivo que no tocamos, y el flag rara vez cambia). 403 si no lo es."""
    user = await users.get_by_id(identity.tenant_id, identity.user_id)
    if user is None or not user.platform_admin:
        raise InsufficientRole()
    return identity
