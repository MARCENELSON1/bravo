from __future__ import annotations

from sqlalchemy import select, update

from app.domain.order.settings import SelfOrderSettings, SelfOrderSettingsRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import TenantORM


class SqlAlchemySelfOrderSettingsRepository(SelfOrderSettingsRepository):
    """Reads/writes the two self-order flags on ``tenants`` directly (no Tenant
    aggregate load). Missing tenant → defaults (disabled, requires confirmation)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get(self, tenant_id: str) -> SelfOrderSettings:
        async with self._session_factory() as db:
            row = (
                await db.execute(
                    select(
                        TenantORM.self_order_enabled,
                        TenantORM.self_order_requires_confirmation,
                        TenantORM.self_order_prepay_required,
                    ).where(TenantORM.id == tenant_id)
                )
            ).one_or_none()
            if row is None:
                return SelfOrderSettings()
            return SelfOrderSettings(
                enabled=bool(row[0]),
                requires_confirmation=bool(row[1]),
                prepay_required=bool(row[2]),
            )

    async def update(self, tenant_id: str, settings: SelfOrderSettings) -> None:
        async with self._session_factory() as db:
            await db.execute(
                update(TenantORM)
                .where(TenantORM.id == tenant_id)
                .values(
                    self_order_enabled=settings.enabled,
                    self_order_requires_confirmation=settings.requires_confirmation,
                    self_order_prepay_required=settings.prepay_required,
                )
            )
