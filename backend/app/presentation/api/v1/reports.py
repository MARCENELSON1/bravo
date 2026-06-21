from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.application.reporting.dashboard import GetDashboardSummary
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.presentation.deps import current_identity
from app.presentation.schemas.reports import DashboardSummaryResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/dashboard", response_model=DashboardSummaryResponse)
@inject
async def dashboard(
    identity: AccessClaims = Depends(current_identity),
    use_case: GetDashboardSummary = Depends(Provide[Container.get_dashboard_summary]),
) -> DashboardSummaryResponse:
    s = await use_case.execute(tenant_id=identity.tenant_id)
    return DashboardSummaryResponse(
        currency=s.currency,
        sales=s.sales,
        expenses=s.expenses,
        net=s.net,
        active_orders=s.active_orders,
        paid_orders=s.paid_orders,
        avg_ticket=s.avg_ticket,
        payment_count=s.payment_count,
    )
