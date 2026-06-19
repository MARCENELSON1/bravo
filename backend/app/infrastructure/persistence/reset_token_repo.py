from __future__ import annotations

from sqlalchemy import select, update

from app.domain.identity.ports import ResetTokenRepository
from app.domain.identity.tokens import PasswordResetToken
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    reset_token_to_domain,
    reset_token_to_orm,
)
from app.infrastructure.persistence.models import PasswordResetTokenORM


class SqlAlchemyResetTokenRepository(ResetTokenRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def add(self, token: PasswordResetToken) -> None:
        async with self._session_factory() as session:
            session.add(reset_token_to_orm(token))

    async def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        async with self._session_factory() as session:
            stmt = select(PasswordResetTokenORM).where(
                PasswordResetTokenORM.token_hash == token_hash
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return reset_token_to_domain(row) if row is not None else None

    async def mark_used(self, token_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(PasswordResetTokenORM)
                .where(PasswordResetTokenORM.id == token_id)
                .values(used=True)
            )

    async def invalidate_for_user(self, tenant_id: str, user_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(PasswordResetTokenORM)
                .where(
                    PasswordResetTokenORM.tenant_id == tenant_id,
                    PasswordResetTokenORM.user_id == user_id,
                    PasswordResetTokenORM.used.is_(False),
                )
                .values(used=True)
            )
