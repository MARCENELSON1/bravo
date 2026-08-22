from __future__ import annotations

from sqlalchemy import select, update

from app.domain.cashier.settings import CashSettings, CashSettingsRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import TenantORM


class SqlAlchemyCashSettingsRepository(CashSettingsRepository):
    """Reads/writes the two cash flags on ``tenants`` directly (no Tenant
    aggregate load). Missing tenant → defaults OFF (parity)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get(self, tenant_id: str) -> CashSettings:
        async with self._session_factory() as db:
            row = (
                await db.execute(
                    select(
                        TenantORM.require_open_cash_session,
                        TenantORM.blind_cash_count,
                    ).where(TenantORM.id == tenant_id)
                )
            ).one_or_none()
            if row is None:
                return CashSettings()
            return CashSettings(
                require_open_cash_session=bool(row[0]),
                blind_cash_count=bool(row[1]),
            )

    async def update(self, tenant_id: str, settings: CashSettings) -> None:
        async with self._session_factory() as db:
            await db.execute(
                update(TenantORM)
                .where(TenantORM.id == tenant_id)
                .values(
                    require_open_cash_session=settings.require_open_cash_session,
                    blind_cash_count=settings.blind_cash_count,
                )
            )
