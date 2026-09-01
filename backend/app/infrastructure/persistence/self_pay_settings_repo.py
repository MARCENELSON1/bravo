from __future__ import annotations

from sqlalchemy import select, update

from app.domain.payment.self_pay_settings import (
    SelfPaySettings,
    SelfPaySettingsRepository,
)
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import TenantORM


class SqlAlchemySelfPaySettingsRepository(SelfPaySettingsRepository):
    """Reads/writes the two self-pay flags on ``tenants`` directly (no Tenant
    aggregate load). Missing tenant → defaults (disabled, tips offered)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get(self, tenant_id: str) -> SelfPaySettings:
        async with self._session_factory() as db:
            row = (
                await db.execute(
                    select(
                        TenantORM.self_pay_enabled,
                        TenantORM.self_pay_tips_enabled,
                    ).where(TenantORM.id == tenant_id)
                )
            ).one_or_none()
            if row is None:
                return SelfPaySettings()
            return SelfPaySettings(
                enabled=bool(row[0]),
                tips_enabled=bool(row[1]),
            )

    async def update(self, tenant_id: str, settings: SelfPaySettings) -> None:
        async with self._session_factory() as db:
            await db.execute(
                update(TenantORM)
                .where(TenantORM.id == tenant_id)
                .values(
                    self_pay_enabled=settings.enabled,
                    self_pay_tips_enabled=settings.tips_enabled,
                )
            )
