from __future__ import annotations

from sqlalchemy import select

from app.domain.advisor.entities import AdvisorSettings
from app.domain.advisor.repository import AdvisorSettingsRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    advisor_settings_to_domain,
    advisor_settings_to_orm,
)
from app.infrastructure.persistence.models import AdvisorSettingsORM


class SqlAlchemyAdvisorSettingsRepository(AdvisorSettingsRepository):
    """Per-tenant cost profile (1:1). Scoped by ``tenant_id`` (RLS + filter)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get(self, tenant_id: str) -> AdvisorSettings | None:
        async with self._session_factory() as session:
            stmt = select(AdvisorSettingsORM).where(
                AdvisorSettingsORM.tenant_id == tenant_id
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return advisor_settings_to_domain(row) if row is not None else None

    async def save(self, settings: AdvisorSettings) -> None:
        async with self._session_factory() as session:
            await session.merge(advisor_settings_to_orm(settings))
