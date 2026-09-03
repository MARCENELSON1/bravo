from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domain.notification.entities import DeviceToken
from app.domain.notification.repository import DeviceTokenRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import DeviceTokenORM


def _to_domain(row: DeviceTokenORM) -> DeviceToken:
    return DeviceToken(
        id=row.id,
        tenant_id=row.tenant_id,
        user_id=row.user_id,
        token=row.token,
        platform=row.platform,
        created_at=row.created_at,
    )


class SqlAlchemyDeviceTokenRepository(DeviceTokenRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def register(self, token: DeviceToken) -> None:
        async with self._session_factory() as session:
            # Upsert por token: el mismo device re-registra sin duplicar (y puede
            # cambiar de dueño si otro user se loguea en ese teléfono).
            stmt = (
                pg_insert(DeviceTokenORM)
                .values(
                    id=token.id,
                    tenant_id=token.tenant_id,
                    user_id=token.user_id,
                    token=token.token,
                    platform=token.platform,
                )
                .on_conflict_do_update(
                    index_elements=[DeviceTokenORM.token],
                    set_={
                        "tenant_id": token.tenant_id,
                        "user_id": token.user_id,
                        "platform": token.platform,
                    },
                )
            )
            await session.execute(stmt)

    async def list_for_user(
        self, tenant_id: str, user_id: str
    ) -> list[DeviceToken]:
        async with self._session_factory() as session:
            rows = (
                await session.execute(
                    select(DeviceTokenORM).where(
                        DeviceTokenORM.tenant_id == tenant_id,
                        DeviceTokenORM.user_id == user_id,
                    )
                )
            ).scalars().all()
            return [_to_domain(r) for r in rows]

    async def delete(self, tenant_id: str, token: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                delete(DeviceTokenORM).where(
                    DeviceTokenORM.tenant_id == tenant_id,
                    DeviceTokenORM.token == token,
                )
            )
