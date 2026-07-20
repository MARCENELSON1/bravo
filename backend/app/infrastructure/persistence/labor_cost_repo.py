from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.application.advisor.report import LaborCostReadModel
from app.domain.timeclock.value_objects import ShiftStatus
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import ShiftORM, UserORM


class SqlAlchemyLaborCostReadModel(LaborCostReadModel):
    """Labor real: turnos CLOSED del período × valor/hora del empleado. Solo
    suman los empleados con rate cargado (los demás no aportan — cargar todos
    los rates para un número completo). Tenant-scoped (RLS + filtro explícito);
    el turno se atribuye al día en que empezó, igual que el staff report."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def total(self, tenant_id: str, since: datetime, until: datetime) -> int:
        async with self._session_factory() as session:
            stmt = (
                select(
                    ShiftORM.clock_in_at,
                    ShiftORM.clock_out_at,
                    UserORM.hourly_rate_amount,
                )
                .join(UserORM, UserORM.id == ShiftORM.user_id)
                .where(
                    ShiftORM.tenant_id == tenant_id,
                    ShiftORM.status == ShiftStatus.CLOSED.value,
                    ShiftORM.clock_in_at >= since,
                    ShiftORM.clock_in_at <= until,
                    UserORM.hourly_rate_amount.is_not(None),
                )
            )
            total = 0
            for cin, cout, rate in (await session.execute(stmt)).all():
                if cout is None or rate is None:
                    continue
                minutes = int((cout - cin).total_seconds() // 60)
                total += minutes * rate // 60
            return total
