from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.application.cashier.dtos import CashReport
from app.application.cashier.use_cases import (
    CloseCashSession,
    GetCurrentCashReport,
    OpenCashSession,
)
from app.container import Container
from app.domain.cashier.entities import CashSession
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.cashier import (
    CashReportLineResponse,
    CashReportResponse,
    CashSessionResponse,
    CloseCashSessionRequest,
    OpenCashSessionRequest,
)

router = APIRouter(prefix="/cashier", tags=["cashier"])

_CASH_ROLES = (Role.CASHIER, Role.MANAGER, Role.OWNER)


def _session_response(session: CashSession) -> CashSessionResponse:
    return CashSessionResponse(
        id=session.id,
        status=session.status.value,
        currency=session.currency,
        opening_float_amount=session.opening_float.amount,
        opened_at=session.opened_at.isoformat() if session.opened_at else None,
    )


def _report_response(report: CashReport) -> CashReportResponse:
    return CashReportResponse(
        session_id=report.session_id,
        status=report.status,
        currency=report.currency,
        opening_float=report.opening_float,
        opened_at=report.opened_at.isoformat() if report.opened_at else None,
        closed_at=report.closed_at.isoformat() if report.closed_at else None,
        lines=[
            CashReportLineResponse(
                method=line.method,
                expected=line.expected,
                tips=line.tips,
                counted=line.counted,
                difference=line.difference,
            )
            for line in report.lines
        ],
        expected_total=report.expected_total,
        counted_total=report.counted_total,
        difference_total=report.difference_total,
        tips_total=report.tips_total,
    )


@router.post("/session/open", response_model=CashSessionResponse)
@inject
async def open_session(
    body: OpenCashSessionRequest,
    identity: AccessClaims = Depends(require_roles(*_CASH_ROLES)),
    use_case: OpenCashSession = Depends(Provide[Container.open_cash_session]),
) -> CashSessionResponse:
    session = await use_case.execute(
        tenant_id=identity.tenant_id,
        opened_by=identity.user_id,
        opening_float_amount=body.opening_float_amount,
        note=body.note,
    )
    return _session_response(session)


@router.get("/session/current", response_model=CashReportResponse | None)
@inject
async def current_session(
    identity: AccessClaims = Depends(require_roles(*_CASH_ROLES)),
    use_case: GetCurrentCashReport = Depends(Provide[Container.get_current_cash_report]),
) -> CashReportResponse | None:
    report = await use_case.execute(tenant_id=identity.tenant_id)
    return _report_response(report) if report is not None else None


@router.post("/session/{session_id}/close", response_model=CashReportResponse)
@inject
async def close_session(
    session_id: str,
    body: CloseCashSessionRequest,
    identity: AccessClaims = Depends(require_roles(*_CASH_ROLES)),
    use_case: CloseCashSession = Depends(Provide[Container.close_cash_session]),
) -> CashReportResponse:
    report = await use_case.execute(
        tenant_id=identity.tenant_id,
        session_id=session_id,
        counted={method.value: amount for method, amount in body.counted.items()},
        closed_by=identity.user_id,
        note=body.note,
    )
    return _report_response(report)
