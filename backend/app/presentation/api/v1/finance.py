from __future__ import annotations

from datetime import datetime

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from app.application.finance.dtos import FinanceOverview
from app.application.finance.use_cases import GetFinanceOverview
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.finance import (
    FinanceDiagnosticResponse,
    FinanceKpiResponse,
    FinanceOverviewResponse,
    ProductMarginResponse,
)

router = APIRouter(prefix="/finance", tags=["finance"])

_FINANCE_ROLES = (Role.OWNER, Role.MANAGER)


def _overview_response(o: FinanceOverview) -> FinanceOverviewResponse:
    return FinanceOverviewResponse(
        currency=o.currency,
        period_days=o.period_days,
        configured=o.configured,
        kpis=[
            FinanceKpiResponse(
                key=k.key,
                kind=k.kind,
                value=k.value,
                previous=k.previous,
                delta=k.delta,
                healthy_low=k.healthy_low,
                healthy_high=k.healthy_high,
                status=k.status,
            )
            for k in o.kpis
        ],
        diagnostics=[
            FinanceDiagnosticResponse(
                code=d.code,
                severity=d.severity,
                bucket=d.bucket,
                title=d.title,
                body=d.body,
                action=d.action,
            )
            for d in o.diagnostics
        ],
        product_margins=[
            ProductMarginResponse(
                product_id=p.product_id,
                product_name=p.product_name,
                units_sold=p.units_sold,
                sales_amount=p.sales_amount,
                margin_amount=p.margin_amount,
            )
            for p in o.product_margins
        ],
        summary=o.summary,
    )


@router.get("/overview", response_model=FinanceOverviewResponse)
@inject
async def get_overview(
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    identity: AccessClaims = Depends(require_roles(*_FINANCE_ROLES)),
    use_case: GetFinanceOverview = Depends(Provide[Container.get_finance_overview]),
) -> FinanceOverviewResponse:
    """Pantalla Finanzas: KPIs vitales con comparativo + diagnósticos + margen
    por producto, en ``[from, to)`` (default: mes en curso)."""
    overview = await use_case.execute(tenant_id=identity.tenant_id, since=since, until=until)
    return _overview_response(overview)
