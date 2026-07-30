from __future__ import annotations

from datetime import datetime

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from app.application.finance.dtos import ExpenseBreakdown, FinanceOverview, ProductDetail
from app.application.finance.snapshots import RebuildFinanceSnapshots
from app.application.finance.use_cases import (
    GetExpenseBreakdown,
    GetFinanceOverview,
    GetProductDetail,
    GetRecentMovements,
)
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.finance import (
    ExpenseBreakdownResponse,
    ExpenseCategoryRowResponse,
    FinanceDiagnosticResponse,
    FinanceKpiResponse,
    FinanceOverviewResponse,
    FinanceProjectionResponse,
    FinanceSnapshotRebuildResponse,
    MovementResponse,
    ProductDetailResponse,
    ProductMarginResponse,
    ProductSaleLineResponse,
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
        projection=(
            FinanceProjectionResponse(
                sales_amount=o.projection.sales_amount,
                net_margin_amount=o.projection.net_margin_amount,
                month_days=o.projection.month_days,
                elapsed_days=o.projection.elapsed_days,
            )
            if o.projection is not None
            else None
        ),
    )


def _detail_response(d: ProductDetail) -> ProductDetailResponse:
    return ProductDetailResponse(
        product_id=d.product_id,
        currency=d.currency,
        units_sold=d.units_sold,
        sales_amount=d.sales_amount,
        food_cost_amount=d.food_cost_amount,
        margin_amount=d.margin_amount,
        lines=[
            ProductSaleLineResponse(
                order_id=line.order_id,
                occurred_at=line.occurred_at,
                quantity=line.quantity,
                line_amount=line.line_amount,
                food_cost_amount=line.food_cost_amount,
                margin_amount=line.margin_amount,
            )
            for line in d.lines
        ],
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


@router.post("/snapshots/rebuild", response_model=FinanceSnapshotRebuildResponse)
@inject
async def rebuild_snapshots(
    identity: AccessClaims = Depends(require_roles(Role.OWNER)),
    use_case: RebuildFinanceSnapshots = Depends(
        Provide[Container.rebuild_finance_snapshots]
    ),
) -> FinanceSnapshotRebuildResponse:
    """Reconstruye los snapshots diarios desde sale_facts (backfill / paridad).
    Correr antes de prender el modo snapshot para un tenant."""
    days = await use_case.execute(tenant_id=identity.tenant_id)
    return FinanceSnapshotRebuildResponse(days=days)


@router.get("/products/{product_id}", response_model=ProductDetailResponse)
@inject
async def get_product_detail(
    product_id: str,
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    identity: AccessClaims = Depends(require_roles(*_FINANCE_ROLES)),
    use_case: GetProductDetail = Depends(Provide[Container.get_product_detail]),
) -> ProductDetailResponse:
    """Drill-down: las líneas de venta de un producto en ``[from, to)``."""
    detail = await use_case.execute(
        tenant_id=identity.tenant_id, product_id=product_id, since=since, until=until
    )
    return _detail_response(detail)


@router.get("/expenses/breakdown", response_model=ExpenseBreakdownResponse)
@inject
async def get_expense_breakdown(
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    identity: AccessClaims = Depends(require_roles(*_FINANCE_ROLES)),
    use_case: GetExpenseBreakdown = Depends(Provide[Container.get_expense_breakdown]),
) -> ExpenseBreakdownResponse:
    """Egresos por categoría en ``[from, to)`` + comparativo con el período previo."""
    b: ExpenseBreakdown = await use_case.execute(
        tenant_id=identity.tenant_id, since=since, until=until
    )
    return ExpenseBreakdownResponse(
        currency=b.currency,
        total=b.total,
        rows=[
            ExpenseCategoryRowResponse(
                category=r.category, amount=r.amount, previous=r.previous, delta=r.delta
            )
            for r in b.rows
        ],
    )


@router.get("/movements", response_model=list[MovementResponse])
@inject
async def get_movements(
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=20, ge=1, le=100),
    identity: AccessClaims = Depends(require_roles(*_FINANCE_ROLES)),
    use_case: GetRecentMovements = Depends(Provide[Container.get_recent_movements]),
) -> list[MovementResponse]:
    """Últimos movimientos (cobros + egresos) en ``[from, to)`` (para modo Hoy/Semana)."""
    rows = await use_case.execute(
        tenant_id=identity.tenant_id, since=since, until=until, limit=limit
    )
    return [
        MovementResponse(
            occurred_at=m.occurred_at,
            kind=m.kind,
            amount=m.amount,
            method=m.method,
            category=m.category,
            description=m.description,
            currency=m.currency,
        )
        for m in rows
    ]
