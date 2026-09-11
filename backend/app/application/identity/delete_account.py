"""Borrar la propia cuenta — requisito 5.1.1(v) de la App Store.

Apple exige que quien puede crear una cuenta desde la app pueda borrarla desde la
app, no por un mail a soporte. Acá eso choca con que la cuenta de un dueño ES el
local: borrar solo su usuario dejaría un negocio con datos y sin nadie que pueda
entrar. Por eso el caso de uso distingue los dos borrados y lo dice antes de
hacerlo, para que el cliente pueda advertir lo que corresponde.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.identity.ports import PasswordHasher, TenantContext
from app.domain.tenant.repository import TenantRepository
from app.domain.user.exceptions import InvalidCredentials, UserNotFound
from app.domain.user.repository import UserRepository
from app.domain.user.value_objects import Role


@dataclass(frozen=True)
class AccountDeletionScope:
    """Qué se va a borrar si esta persona confirma.

    ``deletes_business`` es la diferencia que hay que mostrarle: irse del equipo
    no es lo mismo que dar de baja el local.
    """

    deletes_business: bool
    tenant_name: str


class PreviewAccountDeletion:
    """Qué alcance tiene el borrado, SIN borrar nada. El cliente lo usa para
    redactar la confirmación: no es lo mismo "vas a perder tu acceso" que "vas a
    borrar el local y todo su historial"."""

    def __init__(
        self,
        users: UserRepository,
        tenants: TenantRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._users = users
        self._tenants = tenants
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, user_id: str) -> AccountDeletionScope:
        self._tenant_context.set(tenant_id)
        user = await self._users.get_by_id(tenant_id, user_id)
        if user is None:
            raise UserNotFound()
        tenant = await self._tenants.get_by_id(tenant_id)
        last_owner = (
            user.role is Role.OWNER
            and await self._users.count_active_owners(tenant_id) <= 1
        )
        return AccountDeletionScope(
            deletes_business=last_owner,
            tenant_name=tenant.name if tenant else "",
        )


class DeleteMyAccount:
    """Borra la cuenta de quien la pide. Irreversible.

    Pide la contraseña de nuevo aunque el token sea válido: un teléfono
    desbloqueado sobre la barra no debería poder dar de baja el local de un
    descuido, y es la práctica que Apple espera para una acción destructiva.

    Si es el último dueño, se borra el LOCAL entero (cascada de las 44 claves
    foráneas). Si no, solo su usuario: el resto del equipo sigue trabajando.
    """

    def __init__(
        self,
        users: UserRepository,
        tenants: TenantRepository,
        hasher: PasswordHasher,
        tenant_context: TenantContext,
        preview: PreviewAccountDeletion,
    ) -> None:
        self._users = users
        self._tenants = tenants
        self._hasher = hasher
        self._tenant_context = tenant_context
        self._preview = preview

    async def execute(
        self, *, tenant_id: str, user_id: str, password: str
    ) -> AccountDeletionScope:
        self._tenant_context.set(tenant_id)
        user = await self._users.get_by_id(tenant_id, user_id)
        if user is None:
            raise UserNotFound()
        if user.password_hash is None or not await self._hasher.verify(
            password, user.password_hash
        ):
            raise InvalidCredentials()

        scope = await self._preview.execute(tenant_id=tenant_id, user_id=user_id)
        if scope.deletes_business:
            await self._tenants.delete(tenant_id)
        else:
            await self._users.delete(tenant_id, user_id)
        return scope
