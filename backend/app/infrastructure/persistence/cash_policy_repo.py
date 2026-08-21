from __future__ import annotations

from sqlalchemy import select

from app.domain.cashier.policy import CashSessionPolicy
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import TenantORM


class SqlAlchemyCashSessionPolicy(CashSessionPolicy):
    """Lee ``tenants.require_open_cash_session`` directo (sin cargar el agregado
    Tenant). Tenant faltante → False (no bloquea)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def requires_open_cash_session(self, tenant_id: str) -> bool:
        async with self._session_factory() as db:
            value = (
                await db.execute(
                    select(TenantORM.require_open_cash_session).where(
                        TenantORM.id == tenant_id
                    )
                )
            ).scalar_one_or_none()
            return bool(value)
