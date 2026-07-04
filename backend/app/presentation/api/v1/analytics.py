from __future__ import annotations

from datetime import datetime

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from app.application.analytics.rebuild import RebuildSalesFacts
from app.application.analytics.use_cases import (
    GetPaymentMix,
    GetProductPerformance,
    GetRevenueDaily,
    GetRevenueSummary,
)
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.analytics import (
    PaymentMixRowResponse,
    ProductPerformanceRowResponse,
    RebuildResponse,
    RevenueDailyPointResponse,
    RevenueSummaryResponse,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/revenue/daily", response_model=list[RevenueDailyPointResponse])
@inject
async def get_revenue_daily(
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetRevenueDaily = Depends(Provide[Container.get_revenue_daily]),
) -> list[RevenueDailyPointResponse]:
    points = await use_case.execute(tenant_id=identity.tenant_id, since=since, until=until)
    return [
        RevenueDailyPointResponse(
            day=p.day, sales_amount=p.sales_amount, orders_count=p.orders_count
        )
        for p in points
    ]


@router.get("/revenue", response_model=RevenueSummaryResponse)
@inject
async def get_revenue(
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetRevenueSummary = Depends(Provide[Container.get_revenue_summary]),
) -> RevenueSummaryResponse:
    s = await use_case.execute(tenant_id=identity.tenant_id, since=since, until=until)
    return RevenueSummaryResponse(
        currency=s.currency,
        sales_amount=s.sales_amount,
        collected_amount=s.collected_amount,
        expense_amount=s.expense_amount,
        food_cost_amount=s.food_cost_amount,
        gross_margin_amount=s.gross_margin_amount,
        orders_count=s.orders_count,
        average_ticket_amount=s.average_ticket_amount,
    )


@router.get("/payment-mix", response_model=list[PaymentMixRowResponse])
@inject
async def get_payment_mix(
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetPaymentMix = Depends(Provide[Container.get_payment_mix]),
) -> list[PaymentMixRowResponse]:
    rows = await use_case.execute(tenant_id=identity.tenant_id, since=since, until=until)
    return [
        PaymentMixRowResponse(
            method=r.method, direction=r.direction, amount=r.amount, count=r.count
        )
        for r in rows
    ]


@router.get("/products", response_model=list[ProductPerformanceRowResponse])
@inject
async def get_product_performance(
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=10, ge=1, le=100),
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetProductPerformance = Depends(Provide[Container.get_product_performance]),
) -> list[ProductPerformanceRowResponse]:
    rows = await use_case.execute(
        tenant_id=identity.tenant_id, since=since, until=until, limit=limit
    )
    return [
        ProductPerformanceRowResponse(
            product_id=r.product_id,
            product_name=r.product_name,
            units_sold=r.units_sold,
            sales_amount=r.sales_amount,
            food_cost_amount=r.food_cost_amount,
            margin_amount=r.margin_amount,
            currency=r.currency,
        )
        for r in rows
    ]


@router.post("/rebuild", response_model=RebuildResponse)
@inject
async def rebuild(
    identity: AccessClaims = Depends(require_roles(Role.OWNER)),
    use_case: RebuildSalesFacts = Depends(Provide[Container.rebuild_sales_facts]),
) -> RebuildResponse:
    projected = await use_case.execute(tenant_id=identity.tenant_id)
    return RebuildResponse(projected=projected)
