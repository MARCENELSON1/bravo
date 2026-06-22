from __future__ import annotations

from datetime import datetime

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from app.application.advisor.report import AdvisorReport, GetAdvisorReport
from app.application.advisor.use_cases import GetAdvisorSettings, UpdateAdvisorSettings
from app.container import Container
from app.domain.advisor.entities import AdvisorSettings
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.advisor import (
    AdvisorKpisResponse,
    AdvisorReportResponse,
    AdvisorSettingsResponse,
    NarratedInsightResponse,
    UpdateAdvisorSettingsRequest,
)

router = APIRouter(prefix="/advisor", tags=["advisor"])


def _report_response(report: AdvisorReport) -> AdvisorReportResponse:
    k = report.kpis
    return AdvisorReportResponse(
        kpis=AdvisorKpisResponse(
            currency=k.currency,
            period_days=k.period_days,
            sales_amount=k.sales_amount,
            food_cost_amount=k.food_cost_amount,
            labor_cost_amount=k.labor_cost_amount,
            other_fixed_amount=k.other_fixed_amount,
            waste_amount=k.waste_amount,
            gross_margin_amount=k.gross_margin_amount,
            net_margin_amount=k.net_margin_amount,
            food_cost_ratio_bps=k.food_cost_ratio_bps,
            labor_cost_ratio_bps=k.labor_cost_ratio_bps,
            prime_cost_ratio_bps=k.prime_cost_ratio_bps,
            break_even_amount=k.break_even_amount,
            orders_count=k.orders_count,
            average_ticket_amount=k.average_ticket_amount,
            no_show_rate_bps=k.no_show_rate_bps,
            configured=k.configured,
        ),
        insights=[
            NarratedInsightResponse(
                code=i.code,
                severity=i.severity,
                bucket=i.bucket,
                title=i.title,
                body=i.body,
                action=i.action,
            )
            for i in report.insights
        ],
        summary=report.summary,
        llm_enabled=report.llm_enabled,
    )


def _settings_response(settings: AdvisorSettings | None) -> AdvisorSettingsResponse:
    if settings is None:
        return AdvisorSettingsResponse(
            monthly_labor_cost=0,
            monthly_other_fixed_costs=0,
            target_food_cost_bps=3000,
            currency="ARS",
            configured=False,
        )
    return AdvisorSettingsResponse(
        monthly_labor_cost=settings.monthly_labor_cost.amount,
        monthly_other_fixed_costs=settings.monthly_other_fixed_costs.amount,
        target_food_cost_bps=settings.target_food_cost_bps,
        currency=settings.currency,
        configured=True,
    )


@router.get("/report", response_model=AdvisorReportResponse)
@inject
async def get_report(
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetAdvisorReport = Depends(Provide[Container.get_advisor_report]),
) -> AdvisorReportResponse:
    report = await use_case.execute(tenant_id=identity.tenant_id, since=since, until=until)
    return _report_response(report)


@router.get("/settings", response_model=AdvisorSettingsResponse)
@inject
async def get_settings(
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetAdvisorSettings = Depends(Provide[Container.get_advisor_settings]),
) -> AdvisorSettingsResponse:
    settings = await use_case.execute(tenant_id=identity.tenant_id)
    return _settings_response(settings)


@router.put("/settings", response_model=AdvisorSettingsResponse)
@inject
async def update_settings(
    body: UpdateAdvisorSettingsRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER)),
    use_case: UpdateAdvisorSettings = Depends(Provide[Container.update_advisor_settings]),
) -> AdvisorSettingsResponse:
    settings = await use_case.execute(
        tenant_id=identity.tenant_id,
        monthly_labor_cost=body.monthly_labor_cost,
        monthly_other_fixed_costs=body.monthly_other_fixed_costs,
        target_food_cost_bps=body.target_food_cost_bps,
    )
    return _settings_response(settings)
