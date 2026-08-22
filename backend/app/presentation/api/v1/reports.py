from __future__ import annotations

from datetime import datetime

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Response

from app.application.reporting.dashboard import GetDashboardSummary
from app.application.reporting.exports import ExportReport, ReportExportKind
from app.application.reporting.staff import GetStaffReport
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.csv_export import csv_response
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.reports import (
    DashboardSummaryResponse,
    StaffReportResponse,
    StaffReportRowResponse,
)

router = APIRouter(prefix="/reports", tags=["reports"])

_STAFF_REPORT_ROLES = (Role.OWNER, Role.MANAGER)
_EXPORT_ROLES = (Role.OWNER, Role.MANAGER)

# Nombre de archivo por export (el contador lo reconoce de un vistazo).
_EXPORT_FILENAMES = {
    ReportExportKind.SALES: "ventas-por-dia.csv",
    ReportExportKind.EXPENSES: "gastos.csv",
    ReportExportKind.VAT_SALES: "libro-iva-ventas.csv",
}


@router.get("/dashboard", response_model=DashboardSummaryResponse)
@inject
async def dashboard(
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    identity: AccessClaims = Depends(current_identity),
    use_case: GetDashboardSummary = Depends(Provide[Container.get_dashboard_summary]),
) -> DashboardSummaryResponse:
    s = await use_case.execute(tenant_id=identity.tenant_id, since=since, until=until)
    return DashboardSummaryResponse(
        currency=s.currency,
        sales=s.sales,
        expenses=s.expenses,
        net=s.net,
        active_orders=s.active_orders,
        paid_orders=s.paid_orders,
        avg_ticket=s.avg_ticket,
        payment_count=s.payment_count,
        collected_net=s.collected_net,
        fees_total=s.fees_total,
    )


@router.get("/staff", response_model=StaffReportResponse)
@inject
async def staff_report(
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    identity: AccessClaims = Depends(require_roles(*_STAFF_REPORT_ROLES)),
    use_case: GetStaffReport = Depends(Provide[Container.get_staff_report]),
) -> StaffReportResponse:
    report = await use_case.execute(
        tenant_id=identity.tenant_id, since=since, until=until
    )
    return StaffReportResponse(
        currency=report.currency,
        rows=[
            StaffReportRowResponse(
                user_id=r.user_id,
                email=r.email,
                worked_minutes=r.worked_minutes,
                overtime_minutes=r.overtime_minutes,
                tables_served=r.tables_served,
                sales_amount=r.sales_amount,
                hourly_rate_amount=r.hourly_rate_amount,
                currency=r.currency,
            )
            for r in report.rows
        ],
    )


@router.get("/export/{kind}.csv")
@inject
async def export_csv(
    kind: ReportExportKind,
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    identity: AccessClaims = Depends(require_roles(*_EXPORT_ROLES)),
    use_case: ExportReport = Depends(Provide[Container.export_report]),
) -> Response:
    """CSV para el contador: `sales` (ventas por día), `expenses` (gastos
    itemizados) o `vat_sales` (libro IVA ventas, comprobantes con CAE)."""
    table = await use_case.execute(
        tenant_id=identity.tenant_id, kind=kind, since=since, until=until
    )
    return csv_response(_EXPORT_FILENAMES[kind], table)
