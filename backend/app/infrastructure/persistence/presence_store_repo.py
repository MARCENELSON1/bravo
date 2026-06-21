from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, select

from app.domain.timeclock.exceptions import PresenceTokenReused
from app.domain.timeclock.presence import PresenceUsageStore
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import UsedPresenceTokenORM


class SqlAlchemyPresenceUsageStore(PresenceUsageStore):
    """Single-use + rate-limit backing store. Tenant-scoped (RLS + explicit
    filter). The unique index ``uq_used_presence_token`` is the hard backstop;
    the check-then-insert below turns a same-user replay into a clean error."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def count_recent(self, tenant_id: str, user_id: str, since: datetime) -> int:
        async with self._session_factory() as session:
            stmt = select(func.count()).where(
                UsedPresenceTokenORM.tenant_id == tenant_id,
                UsedPresenceTokenORM.user_id == user_id,
                UsedPresenceTokenORM.created_at >= since,
            )
            return int((await session.execute(stmt)).scalar_one())

    async def mark_used(self, tenant_id: str, time_step: int, user_id: str) -> None:
        async with self._session_factory() as session:
            existing = (
                await session.execute(
                    select(UsedPresenceTokenORM.id).where(
                        UsedPresenceTokenORM.tenant_id == tenant_id,
                        UsedPresenceTokenORM.time_step == time_step,
                        UsedPresenceTokenORM.user_id == user_id,
                    )
                )
            ).scalar_one_or_none()
            if existing is not None:
                raise PresenceTokenReused()
            session.add(
                UsedPresenceTokenORM(
                    id=str(uuid4()),
                    tenant_id=tenant_id,
                    time_step=time_step,
                    user_id=user_id,
                )
            )
