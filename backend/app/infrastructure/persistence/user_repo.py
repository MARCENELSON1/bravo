from __future__ import annotations

from sqlalchemy import select

from app.domain.user.entities import User
from app.domain.user.repository import UserRepository
from app.domain.user.value_objects import Role
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import user_to_domain, user_to_orm
from app.infrastructure.persistence.models import UserORM


class SqlAlchemyUserRepository(UserRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, tenant_id: str, user_id: str) -> User | None:
        async with self._session_factory() as session:
            stmt = select(UserORM).where(UserORM.id == user_id, UserORM.tenant_id == tenant_id)
            row = (await session.execute(stmt)).scalar_one_or_none()
            return user_to_domain(row) if row is not None else None

    async def get_by_email(self, tenant_id: str, email: str) -> User | None:
        async with self._session_factory() as session:
            stmt = select(UserORM).where(
                UserORM.tenant_id == tenant_id, UserORM.email == email
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return user_to_domain(row) if row is not None else None

    async def names_by_ids(self, tenant_id: str, ids: set[str]) -> dict[str, str]:
        if not ids:
            return {}
        async with self._session_factory() as session:
            rows = (
                await session.execute(
                    select(UserORM.id, UserORM.name, UserORM.email).where(
                        UserORM.tenant_id == tenant_id, UserORM.id.in_(ids)
                    )
                )
            ).all()
            return {uid: (name or email) for uid, name, email in rows}

    async def roles_by_ids(self, tenant_id: str, ids: set[str]) -> dict[str, Role]:
        if not ids:
            return {}
        async with self._session_factory() as session:
            rows = (
                await session.execute(
                    select(UserORM.id, UserORM.role).where(
                        UserORM.tenant_id == tenant_id,
                        UserORM.id.in_(ids),
                        UserORM.active.is_(True),
                    )
                )
            ).all()
            return {uid: Role(role) for uid, role in rows}

    async def add(self, user: User) -> None:
        async with self._session_factory() as session:
            session.add(user_to_orm(user))

    async def save(self, user: User) -> None:
        async with self._session_factory() as session:
            await session.merge(user_to_orm(user))
