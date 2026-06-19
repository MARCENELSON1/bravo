from __future__ import annotations

from sqlalchemy import select, update

from app.domain.identity.ports import InvitationRepository
from app.domain.identity.tokens import Invitation
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    invitation_to_domain,
    invitation_to_orm,
)
from app.infrastructure.persistence.models import InvitationORM


class SqlAlchemyInvitationRepository(InvitationRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def add(self, invitation: Invitation) -> None:
        async with self._session_factory() as session:
            session.add(invitation_to_orm(invitation))

    async def get_by_hash(self, token_hash: str) -> Invitation | None:
        async with self._session_factory() as session:
            stmt = select(InvitationORM).where(InvitationORM.token_hash == token_hash)
            row = (await session.execute(stmt)).scalar_one_or_none()
            return invitation_to_domain(row) if row is not None else None

    async def mark_used(self, invitation_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(InvitationORM)
                .where(InvitationORM.id == invitation_id)
                .values(used=True)
            )
