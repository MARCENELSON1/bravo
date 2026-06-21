from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func, select

from app.application.reporting.staff import (
    StaffReport,
    StaffReportReadModel,
    StaffReportRow,
)
from app.domain.order.value_objects import OrderStatus
from app.domain.timeclock.hours import daily_overtime
from app.domain.timeclock.value_objects import ShiftStatus
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import (
    OrderItemORM,
    OrderORM,
    ShiftORM,
    TenantORM,
    UserORM,
)


class SqlAlchemyStaffReportReadModel(StaffReportReadModel):
    """Per-employee report: hours + overtime from shifts (overtime aggregated in
    Python with the domain ``daily_overtime``), crossed with tables/sales from
    orders via ``waiter_id``. Tenant-scoped (RLS + explicit filter); read-only.

    Days are bucketed by the clock-in date (UTC); a shift that crosses midnight
    counts to the day it started — good enough for the MVP labor report.
    """

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def report(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> StaffReport:
        async with self._session_factory() as session:
            tenant = (
                await session.execute(
                    select(
                        TenantORM.currency, TenantORM.standard_workday_minutes
                    ).where(TenantORM.id == tenant_id)
                )
            ).one_or_none()
            currency, standard = tenant if tenant is not None else ("ARS", 480)

            # Closed shifts in the period → minutes per (user, day).
            shift_stmt = select(
                ShiftORM.user_id, ShiftORM.clock_in_at, ShiftORM.clock_out_at
            ).where(
                ShiftORM.tenant_id == tenant_id,
                ShiftORM.status == ShiftStatus.CLOSED.value,
            )
            if since is not None:
                shift_stmt = shift_stmt.where(ShiftORM.clock_in_at >= since)
            if until is not None:
                shift_stmt = shift_stmt.where(ShiftORM.clock_in_at <= until)
            per_user_day: dict[str, dict[date, int]] = {}
            for user_id, cin, cout in (await session.execute(shift_stmt)).all():
                if cout is None:
                    continue
                minutes = int((cout - cin).total_seconds() // 60)
                day_map = per_user_day.setdefault(user_id, {})
                day_map[cin.date()] = day_map.get(cin.date(), 0) + minutes

            # Sales + distinct tables per waiter, over PAID orders in the period.
            orders_filter = [
                OrderORM.tenant_id == tenant_id,
                OrderORM.status == OrderStatus.PAID.value,
            ]
            if since is not None:
                orders_filter.append(OrderORM.created_at >= since)
            if until is not None:
                orders_filter.append(OrderORM.created_at <= until)

            sales_stmt = (
                select(
                    OrderORM.waiter_id,
                    func.coalesce(
                        func.sum(OrderItemORM.unit_price_amount * OrderItemORM.quantity),
                        0,
                    ),
                )
                .select_from(OrderORM)
                .join(OrderItemORM, OrderItemORM.order_id == OrderORM.id)
                .where(*orders_filter)
                .group_by(OrderORM.waiter_id)
            )
            sales_by_user = {
                waiter_id: int(total)
                for waiter_id, total in (await session.execute(sales_stmt)).all()
            }

            tables_stmt = (
                select(OrderORM.waiter_id, func.count(func.distinct(OrderORM.table_id)))
                .where(*orders_filter)
                .group_by(OrderORM.waiter_id)
            )
            tables_by_user = {
                waiter_id: int(count)
                for waiter_id, count in (await session.execute(tables_stmt)).all()
            }

            user_ids = set(per_user_day) | set(sales_by_user) | set(tables_by_user)
            if not user_ids:
                return StaffReport(currency=currency, rows=[])

            emails = {
                uid: email
                for uid, email in (
                    await session.execute(
                        select(UserORM.id, UserORM.email).where(
                            UserORM.tenant_id == tenant_id, UserORM.id.in_(user_ids)
                        )
                    )
                ).all()
            }

            rows = [
                StaffReportRow(
                    user_id=uid,
                    email=emails.get(uid, ""),
                    worked_minutes=sum(per_user_day.get(uid, {}).values()),
                    overtime_minutes=sum(
                        daily_overtime(m, standard)
                        for m in per_user_day.get(uid, {}).values()
                    ),
                    tables_served=tables_by_user.get(uid, 0),
                    sales_amount=sales_by_user.get(uid, 0),
                    currency=currency,
                )
                for uid in user_ids
            ]
            rows.sort(key=lambda r: r.email)
            return StaffReport(currency=currency, rows=rows)
