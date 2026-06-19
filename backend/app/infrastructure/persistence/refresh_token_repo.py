from __future__ import annotations

from sqlalchemy import select, update

from app.domain.identity.ports import RefreshTokenRepository
from app.domain.identity.tokens import RefreshToken
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    refresh_token_to_domain,
    refresh_token_to_orm,
)
from app.infrastructure.persistence.models import RefreshTokenORM


class SqlAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def add(self, token: RefreshToken) -> None:
        async with self._session_factory() as session:
            session.add(refresh_token_to_orm(token))

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        async with self._session_factory() as session:
            stmt = select(RefreshTokenORM).where(RefreshTokenORM.token_hash == token_hash)
            row = (await session.execute(stmt)).scalar_one_or_none()
            return refresh_token_to_domain(row) if row is not None else None

    async def revoke(self, token_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(RefreshTokenORM)
                .where(RefreshTokenORM.id == token_id)
                .values(revoked=True)
            )

    async def revoke_all_for_user(self, tenant_id: str, user_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(RefreshTokenORM)
                .where(
                    RefreshTokenORM.tenant_id == tenant_id,
                    RefreshTokenORM.user_id == user_id,
                )
                .values(revoked=True)
            )
