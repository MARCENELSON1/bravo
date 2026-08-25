"""Outbox de reportes de sales tax (TaxJar AutoFile). Tenant-scoped (RLS + filtro
explícito). El enqueue es idempotente por (tenant, order); el drain marca cada
fila SENT o FAILED (las FAILED se reintentan)."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.application.tax.reporting import PendingTaxReport, TaxReportLedger
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import TaxReportORM

_RETRYABLE = ("PENDING", "FAILED")


class SqlAlchemyTaxReportLedger(TaxReportLedger):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def enqueue(self, tenant_id: str, order_id: str) -> None:
        async with self._session_factory() as session:
            stmt = (
                pg_insert(TaxReportORM)
                .values(id=str(uuid4()), tenant_id=tenant_id, order_id=order_id)
                .on_conflict_do_nothing(constraint="uq_tax_reports_tenant_order")
            )
            await session.execute(stmt)

    async def list_pending(
        self, tenant_id: str, *, limit: int = 100
    ) -> list[PendingTaxReport]:
        async with self._session_factory() as session:
            stmt = (
                select(TaxReportORM)
                .where(
                    TaxReportORM.tenant_id == tenant_id,
                    TaxReportORM.status.in_(_RETRYABLE),
                )
                .order_by(TaxReportORM.created_at)
                .limit(limit)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [
                PendingTaxReport(
                    id=r.id, order_id=r.order_id, occurred_at=r.created_at.isoformat()
                )
                for r in rows
            ]

    async def mark_sent(self, report_id: str, external_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(TaxReportORM)
                .where(TaxReportORM.id == report_id)
                .values(status="SENT", external_id=external_id, last_error=None)
            )

    async def mark_failed(self, report_id: str, error: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(TaxReportORM)
                .where(TaxReportORM.id == report_id)
                .values(
                    status="FAILED",
                    attempts=TaxReportORM.attempts + 1,
                    last_error=error,
                )
            )
