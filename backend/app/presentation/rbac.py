from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Depends

from app.domain.identity.tokens import AccessClaims
from app.domain.user.exceptions import InsufficientRole
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity


def require_roles(*roles: Role) -> Callable[[AccessClaims], Awaitable[AccessClaims]]:
    """Dependency factory that allows only the given roles (else 403)."""

    async def checker(identity: AccessClaims = Depends(current_identity)) -> AccessClaims:
        if identity.role not in roles:
            raise InsufficientRole()
        return identity

    return checker
