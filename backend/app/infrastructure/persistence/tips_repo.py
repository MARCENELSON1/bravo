from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select

from app.application.cashier.tips import (
    TIP_PAYOUT_CATEGORY,
    TipsReadModel,
    TipsReport,
    TipsReportRow,
)
from app.domain.cashier.tip_payout import TipPayout, TipPayoutRepository
from app.domain.payment.value_objects import PaymentDirection, PaymentStatus
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import (
    OrderORM,
    PaymentORM,
    TenantORM,
    TipPayoutORM,
    UserORM,
)


class SqlAlchemyTipPayoutRepository(TipPayoutRepository):
    """Persiste liquidaciones en el ledger ``tip_payouts`` (tenant-scoped + RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def add(self, payout: TipPayout) -> None:
        async with self._session_factory() as db:
            db.add(
                TipPayoutORM(
                    id=payout.id,
                    tenant_id=payout.tenant_id,
                    waiter_id=payout.waiter_id,
                    amount=payout.amount,
                    currency=payout.currency,
                    method=payout.method,
                )
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

            # Guarda D: sumar las liquidaciones del ledger nuevo (tip_payouts) a las
            # viejas (egreso 'Propinas'), sin reescribir historia. Ventana propia por
            # created_at del payout.
            payout_stmt = (
                select(
                    TipPayoutORM.waiter_id,
                    func.coalesce(func.sum(TipPayoutORM.amount), 0),
                )
                .where(TipPayoutORM.tenant_id == tenant_id)
                .group_by(TipPayoutORM.waiter_id)
            )
            if since is not None:
                payout_stmt = payout_stmt.where(TipPayoutORM.created_at >= since)
            if until is not None:
                payout_stmt = payout_stmt.where(TipPayoutORM.created_at < until)
            for wid, total in (await session.execute(payout_stmt)).all():
                paid[wid] = paid.get(wid, 0) + int(total)

            waiter_ids = set(earned) | set(paid)
            # Guarda D: mostramos el nombre del mozo (fallback email), no el UUID.
            names: dict[str, str] = {}
            if waiter_ids:
                name_rows = (
                    await session.execute(
                        select(UserORM.id, UserORM.name, UserORM.email).where(
                            UserORM.tenant_id == tenant_id, UserORM.id.in_(waiter_ids)
                        )
                    )
                ).all()
                names = {uid: (name or email) for uid, name, email in name_rows}

        rows = [
            TipsReportRow(
                waiter_id=wid,
                waiter_name=names.get(wid, "—"),
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
