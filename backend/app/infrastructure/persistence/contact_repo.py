from __future__ import annotations

from datetime import datetime

from sqlalchemy import distinct, select

from app.domain.contact.entities import ContactLog
from app.domain.contact.repository import ContactLogRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import ContactLogORM


class SqlAlchemyContactLogRepository(ContactLogRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def add(self, log: ContactLog) -> None:
        async with self._session_factory() as db:
            db.add(
                ContactLogORM(
                    id=log.id,
                    tenant_id=log.tenant_id,
                    customer_id=log.customer_id,
                    reason=log.reason,
                    contacted_by=log.contacted_by,
                )
            )

    async def recent_customer_ids(
        self, tenant_id: str, *, since: datetime
    ) -> list[str]:
        async with self._session_factory() as db:
            rows = (
                await db.execute(
                    select(distinct(ContactLogORM.customer_id)).where(
                        ContactLogORM.tenant_id == tenant_id,
                        ContactLogORM.contacted_at >= since,
                    )
                )
            ).scalars().all()
            return list(rows)
