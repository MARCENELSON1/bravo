from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select

from app.application.cashier.tips import (
    TIP_PAYOUT_CATEGORY,
    TipsReadModel,
    TipsReport,
    TipsReportRow,
)
from app.domain.payment.value_objects import PaymentDirection, PaymentStatus
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import (
    OrderORM,
    PaymentORM,
    TenantORM,
    UserORM,
)


class SqlAlchemyTipsReadModel(TipsReadModel):
    """Propinas ganadas por mozo (cobros CONFIRMED atribuidos por ``Order.waiter_id``)
    cruzadas con lo liquidado (egresos 'Propinas' por ``counterparty``). Tenant-scoped
    (RLS + filtro explícito); solo lectura. Las propinas REFUNDED no cuentan (igual
    que en el arqueo). Ventana ``[since, until)`` por ``created_at`` del pago."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def report(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> TipsReport:
        async with self._session_factory() as session:
            currency_row = (
                await session.execute(
                    select(TenantORM.currency).where(TenantORM.id == tenant_id)
                )
            ).scalar_one_or_none()
            currency = currency_row or "ARS"

            # Ganado: propina de cobros CONFIRMED, atribuida por la orden al mozo.
            earned_stmt = (
                select(
                    OrderORM.waiter_id,
                    func.coalesce(func.sum(PaymentORM.tip_amount), 0),
                )
                .join(OrderORM, OrderORM.id == PaymentORM.order_id)
                .where(
                    PaymentORM.tenant_id == tenant_id,
                    PaymentORM.direction == PaymentDirection.INFLOW.value,
                    PaymentORM.status == PaymentStatus.CONFIRMED.value,
                    PaymentORM.tip_amount > 0,
                )
                .group_by(OrderORM.waiter_id)
            )
            earned_stmt = self._window(earned_stmt, since, until)

            # Liquidado: egreso 'Propinas' a nombre del mozo (counterparty=waiter_id).
            paid_stmt = (
                select(
                    PaymentORM.counterparty,
                    func.coalesce(func.sum(PaymentORM.amount), 0),
                )
                .where(
                    PaymentORM.tenant_id == tenant_id,
                    PaymentORM.direction == PaymentDirection.OUTFLOW.value,
                    PaymentORM.status == PaymentStatus.CONFIRMED.value,
                    PaymentORM.category == TIP_PAYOUT_CATEGORY,
                    PaymentORM.counterparty.is_not(None),
                )
                .group_by(PaymentORM.counterparty)
            )
            paid_stmt = self._window(paid_stmt, since, until)

            earned = {wid: int(total) for wid, total in (await session.execute(earned_stmt)).all()}
            paid = {cp: int(total) for cp, total in (await session.execute(paid_stmt)).all()}

            waiter_ids = set(earned) | set(paid)
            emails: dict[str, str] = {}
            if waiter_ids:
                email_rows = (
                    await session.execute(
                        select(UserORM.id, UserORM.email).where(
                            UserORM.tenant_id == tenant_id, UserORM.id.in_(waiter_ids)
                        )
                    )
                ).all()
                emails = {uid: email for uid, email in email_rows}

        rows = [
            TipsReportRow(
                waiter_id=wid,
                waiter_email=emails.get(wid, "—"),
                earned=earned.get(wid, 0),
                paid=paid.get(wid, 0),
                pending=earned.get(wid, 0) - paid.get(wid, 0),
            )
            for wid in waiter_ids
        ]
        rows.sort(key=lambda r: r.pending, reverse=True)
        return TipsReport(
            currency=currency,
            rows=rows,
            earned_total=sum(earned.values()),
            paid_total=sum(paid.values()),
            pending_total=sum(earned.values()) - sum(paid.values()),
        )

    @staticmethod
    def _window(stmt, since: datetime | None, until: datetime | None):  # type: ignore[no-untyped-def]
        if since is not None:
            stmt = stmt.where(PaymentORM.created_at >= since)
        if until is not None:
            stmt = stmt.where(PaymentORM.created_at < until)
        return stmt
