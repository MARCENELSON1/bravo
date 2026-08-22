from __future__ import annotations

from sqlalchemy import select

from app.domain.cashier.entities import CashMovement
from app.domain.cashier.repository import CashMovementRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    cash_movement_to_domain,
    cash_movement_to_orm,
)
from app.infrastructure.persistence.models import CashMovementORM


class SqlAlchemyCashMovementRepository(CashMovementRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def add(self, movement: CashMovement) -> None:
        async with self._session_factory() as db:
            db.add(cash_movement_to_orm(movement))

    async def list_for_session(
        self, tenant_id: str, cash_session_id: str
    ) -> list[CashMovement]:
        async with self._session_factory() as db:
            rows = (
                await db.execute(
                    select(CashMovementORM)
                    .where(
                        CashMovementORM.tenant_id == tenant_id,
                        CashMovementORM.cash_session_id == cash_session_id,
                    )
                    .order_by(CashMovementORM.created_at.asc())
                )
            ).scalars().all()
            return [cash_movement_to_domain(row) for row in rows]
