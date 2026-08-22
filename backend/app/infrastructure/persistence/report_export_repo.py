from __future__ import annotations

from datetime import datetime

from sqlalchemy import distinct, func, select

from app.application.reporting.exports import ExportTable, ReportExportReadModel
from app.domain.invoice.value_objects import InvoiceStatus
from app.domain.payment.value_objects import PaymentDirection, PaymentStatus
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import (
    InvoiceORM,
    PaymentORM,
    SaleFactORM,
)

_OTROS = "Otros"


def _ar(minor: int | None) -> str:
    """Minor units → AR decimal string with a comma (e.g. 150000 → '1500,00')."""
    v = int(minor or 0)
    sign = "-" if v < 0 else ""
    v = abs(v)
    return f"{sign}{v // 100},{v % 100:02d}"


def _day(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d") if dt is not None else ""


def _stamp(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M") if dt is not None else ""


class SqlAlchemyReportExportReadModel(ReportExportReadModel):
    """The three accountant exports as SQL over the existing money tables. Every
    query is tenant-scoped (RLS + explicit filter); read-only."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def sales_by_day(
        self, tenant_id: str, *, since: datetime | None, until: datetime | None
    ) -> ExportTable:
        async with self._session_factory() as db:
            day = func.date_trunc("day", SaleFactORM.occurred_at).label("day")
            stmt = (
                select(
                    day,
                    func.count(distinct(SaleFactORM.order_id)),
                    func.coalesce(func.sum(SaleFactORM.quantity), 0),
                    func.coalesce(func.sum(SaleFactORM.line_amount), 0),
                    func.coalesce(func.sum(SaleFactORM.food_cost_amount), 0),
                )
                .where(SaleFactORM.tenant_id == tenant_id)
                .group_by(day)
                .order_by(day)
            )
            if since is not None:
                stmt = stmt.where(SaleFactORM.occurred_at >= since)
            if until is not None:
                stmt = stmt.where(SaleFactORM.occurred_at <= until)
            rows = (await db.execute(stmt)).all()
        return ExportTable(
            headers=["Fecha", "Órdenes", "Unidades", "Ventas", "Costo de insumos"],
            rows=[
                [_day(d), str(int(orders)), str(int(units)), _ar(sales), _ar(food)]
                for d, orders, units, sales, food in rows
            ],
        )

    async def expenses(
        self, tenant_id: str, *, since: datetime | None, until: datetime | None
    ) -> ExportTable:
        async with self._session_factory() as db:
            stmt = (
                select(
                    PaymentORM.created_at,
                    PaymentORM.category,
                    PaymentORM.method,
                    PaymentORM.amount,
                    PaymentORM.description,
                )
                .where(
                    PaymentORM.tenant_id == tenant_id,
                    PaymentORM.direction == PaymentDirection.OUTFLOW.value,
                    PaymentORM.status == PaymentStatus.CONFIRMED.value,
                )
                .order_by(PaymentORM.created_at)
            )
            if since is not None:
                stmt = stmt.where(PaymentORM.created_at >= since)
            if until is not None:
                stmt = stmt.where(PaymentORM.created_at <= until)
            rows = (await db.execute(stmt)).all()
        return ExportTable(
            headers=["Fecha", "Rubro", "Medio", "Monto", "Detalle"],
            rows=[
                [_stamp(created), category or _OTROS, method, _ar(amount), description or ""]
                for created, category, method, amount, description in rows
            ],
        )

    async def vat_sales(
        self, tenant_id: str, *, since: datetime | None, until: datetime | None
    ) -> ExportTable:
        async with self._session_factory() as db:
            stmt = (
                select(
                    InvoiceORM.issued_at,
                    InvoiceORM.type,
                    InvoiceORM.point_of_sale,
                    InvoiceORM.number,
                    InvoiceORM.doc_type,
                    InvoiceORM.doc_number,
                    InvoiceORM.net_amount,
                    InvoiceORM.vat_amount,
                    InvoiceORM.total_amount,
                    InvoiceORM.cae,
                )
                .where(
                    InvoiceORM.tenant_id == tenant_id,
                    InvoiceORM.status == InvoiceStatus.AUTHORIZED.value,
                )
                .order_by(InvoiceORM.issued_at)
            )
            if since is not None:
                stmt = stmt.where(InvoiceORM.issued_at >= since)
            if until is not None:
                stmt = stmt.where(InvoiceORM.issued_at <= until)
            rows = (await db.execute(stmt)).all()
        return ExportTable(
            headers=[
                "Fecha", "Tipo", "Punto de venta", "Número", "Tipo doc", "Nro doc",
                "Neto", "IVA", "Total", "CAE",
            ],
            rows=[
                [
                    _day(issued), type_, str(int(pos)),
                    str(int(number)) if number is not None else "",
                    doc_type, doc_number, _ar(net), _ar(vat), _ar(total), cae or "",
                ]
                for (
                    issued, type_, pos, number, doc_type, doc_number, net, vat, total, cae
                ) in rows
            ],
        )
