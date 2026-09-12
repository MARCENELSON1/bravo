from abc import ABC, abstractmethod

from app.domain.user.entities import User
from app.domain.user.value_objects import Role


class UserRepository(ABC):
    """Port for user persistence. Every method is scoped by ``tenant_id``."""

    @abstractmethod
    async def get_by_id(self, tenant_id: str, user_id: str) -> User | None: ...

    @abstractmethod
    async def roles_by_ids(self, tenant_id: str, ids: set[str]) -> dict[str, Role]:
        """Bulk role lookup for a set of active user ids (Fase 3 auto-assign filters
        the clocked-in staff to WAITER). Inactive users are omitted."""
        ...

    @abstractmethod
    async def get_by_email(self, tenant_id: str, email: str) -> User | None: ...

    @abstractmethod
    async def names_by_ids(
        self, tenant_id: str, ids: set[str]
    ) -> dict[str, str]:
        """Bulk display-name lookup (name, falling back to email) for a set of
        user ids. Used by read models (e.g. the floor) to avoid N+1 queries."""
        ...

    @abstractmethod
    async def add(self, user: User) -> None: ...

    @abstractmethod
    async def save(self, user: User) -> None: ...

    @abstractmethod
    async def delete(self, tenant_id: str, user_id: str) -> None:
        """Borra la cuenta de una persona. Las filas que le pertenecen (fichajes,
        tokens de dispositivo) caen por CASCADE; las referencias históricas
        —quién cobró, quién atendió una mesa— quedan con el id huérfano a
        propósito: la venta ocurrió y el libro no se reescribe."""

    @abstractmethod
    async def count_active_owners(self, tenant_id: str) -> int:
        """Cuántos OWNER activos quedan. Si el que se va es el último, borrar solo
        su usuario dejaría un local sin nadie que pueda administrarlo."""
