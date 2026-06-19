from __future__ import annotations

from app.domain.identity.ports import AuditRepository
from app.domain.identity.tokens import AuthAuditEntry
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import audit_to_orm


class SqlAlchemyAuditRepository(AuditRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def record(self, entry: AuthAuditEntry) -> None:
        async with self._session_factory() as session:
            session.add(audit_to_orm(entry))
