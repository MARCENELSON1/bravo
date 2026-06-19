from __future__ import annotations

from sqlalchemy import select

from app.domain.user.entities import User
from app.domain.user.repository import UserRepository
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

    async def add(self, user: User) -> None:
        async with self._session_factory() as session:
            session.add(user_to_orm(user))

    async def save(self, user: User) -> None:
        async with self._session_factory() as session:
            await session.merge(user_to_orm(user))
