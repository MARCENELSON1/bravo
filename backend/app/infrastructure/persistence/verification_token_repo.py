from __future__ import annotations

from sqlalchemy import select, update

from app.domain.identity.ports import VerificationTokenRepository
from app.domain.identity.tokens import EmailVerificationToken
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    verification_token_to_domain,
    verification_token_to_orm,
)
from app.infrastructure.persistence.models import EmailVerificationTokenORM


class SqlAlchemyVerificationTokenRepository(VerificationTokenRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def add(self, token: EmailVerificationToken) -> None:
        async with self._session_factory() as session:
            session.add(verification_token_to_orm(token))

    async def get_by_hash(self, token_hash: str) -> EmailVerificationToken | None:
        async with self._session_factory() as session:
            stmt = select(EmailVerificationTokenORM).where(
                EmailVerificationTokenORM.token_hash == token_hash
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return verification_token_to_domain(row) if row is not None else None

    async def mark_used(self, token_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(EmailVerificationTokenORM)
                .where(EmailVerificationTokenORM.id == token_id)
                .values(used=True)
            )
