"""Set an employee's hourly rate (Pantalla Finanzas Tanda D)."""

from __future__ import annotations

from app.domain.identity.ports import TenantContext
from app.domain.user.entities import User
from app.domain.user.exceptions import UserNotFound
from app.domain.user.repository import UserRepository


class SetUserHourlyRate:
    """Upsert del valor/hora de un empleado (None lo borra → el labor de ese
    empleado vuelve a no aportar y rige el fallback mensual del Asesor)."""

    def __init__(self, users: UserRepository, tenant_context: TenantContext) -> None:
        self._users = users
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, user_id: str, hourly_rate_amount: int | None
    ) -> User:
        self._tenant_context.set(tenant_id)
        user = await self._users.get_by_id(tenant_id, user_id)
        if user is None:
            raise UserNotFound()
        user.hourly_rate_amount = hourly_rate_amount
        await self._users.save(user)
        return user
