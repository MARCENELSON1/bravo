"""Who am I, with names: user (email + name) and tenant (display name).

The access token only carries ids/role (see ``/ping``); the dashboard greeting
and the topbar need the human-facing names, so this reads them from the DB.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.identity.ports import TenantContext
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.tenant.repository import TenantRepository
from app.domain.user.exceptions import UserNotFound
from app.domain.user.repository import UserRepository


@dataclass(frozen=True)
class MyProfile:
    user_id: str
    tenant_id: str
    role: str
    email: str
    name: str | None
    tenant_name: str


class GetMyProfile:
    def __init__(
        self,
        users: UserRepository,
        tenants: TenantRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._users = users
        self._tenants = tenants
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, user_id: str) -> MyProfile:
        self._tenant_context.set(tenant_id)
        user = await self._users.get_by_id(tenant_id, user_id)
        if user is None:
            raise UserNotFound()
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFound()
        return MyProfile(
            user_id=user.id,
            tenant_id=tenant.id,
            role=user.role.value,
            email=str(user.email),
            name=user.name,
            tenant_name=tenant.name,
        )
