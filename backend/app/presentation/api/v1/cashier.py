from __future__ import annotations

from datetime import datetime

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from app.application.cashier.dtos import CashReport
from app.application.cashier.tips import GetTipsReport, PayTips, TipsReport
from app.application.cashier.use_cases import (
    CloseCashSession,
    GetCurrentCashReport,
    OpenCashSession,
    RegisterCashMovement,
)
from app.container import Container
from app.domain.cashier.entities import CashSession
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.cashier import (
    CashMovementRequest,
    CashMovementResponse,
    CashMovementRowResponse,
    CashReportLineResponse,
    CashReportResponse,
    CashSessionResponse,
    CloseCashSessionRequest,
    OpenCashSessionRequest,
    TipPayoutRequest,
    TipPayoutResponse,
    TipsReportResponse,
    TipsReportRowResponse,
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
        movements=[
            CashMovementRowResponse(
                id=mv.id,
                kind=mv.kind,
                amount=mv.amount,
                signed_amount=mv.signed_amount,
                reason=mv.reason,
                created_at=mv.created_at.isoformat() if mv.created_at else None,
            )
            for mv in report.movements
        ],
        cash_in_total=report.cash_in_total,
        cash_out_total=report.cash_out_total,
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


@router.post("/movements", response_model=CashMovementResponse)
@inject
async def register_movement(
    body: CashMovementRequest,
    identity: AccessClaims = Depends(require_roles(*_CASH_ROLES)),
    use_case: RegisterCashMovement = Depends(Provide[Container.register_cash_movement]),
) -> CashMovementResponse:
    """Registrar una sangría / ingreso / pago en efectivo sobre la caja abierta
    (ajusta el esperado del arqueo). Requiere una caja abierta."""
    movement = await use_case.execute(
        tenant_id=identity.tenant_id,
        kind=body.kind.value,
        amount=body.amount,
        created_by=identity.user_id,
        reason=body.reason,
    )
    return CashMovementResponse(
        id=movement.id,
        kind=movement.kind.value,
        amount=movement.amount.amount,
        signed_amount=movement.signed_amount,
        currency=movement.amount.currency,
        reason=movement.reason,
    )


def _tips_response(report: TipsReport) -> TipsReportResponse:
    return TipsReportResponse(
        currency=report.currency,
        rows=[
            TipsReportRowResponse(
                waiter_id=row.waiter_id,
                waiter_name=row.waiter_name,
                earned=row.earned,
                paid=row.paid,
                pending=row.pending,
            )
            for row in report.rows
        ],
        earned_total=report.earned_total,
        paid_total=report.paid_total,
        pending_total=report.pending_total,
    )


@router.get("/tips/report", response_model=TipsReportResponse)
@inject
async def tips_report(
    identity: AccessClaims = Depends(require_roles(*_CASH_ROLES)),
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    use_case: GetTipsReport = Depends(Provide[Container.get_tips_report]),
) -> TipsReportResponse:
    """Propinas ganadas vs liquidadas por mozo en ``[from, to)`` (propina por mozo)."""
    report = await use_case.execute(tenant_id=identity.tenant_id, since=since, until=until)
    return _tips_response(report)


@router.post("/tips/payout", response_model=TipPayoutResponse)
@inject
async def pay_tips(
    body: TipPayoutRequest,
    identity: AccessClaims = Depends(require_roles(*_CASH_ROLES)),
    use_case: PayTips = Depends(Provide[Container.pay_tips]),
) -> TipPayoutResponse:
    """Liquidar propinas a un mozo: pasivo en el ledger (NO egreso → no pega en el
    resultado del mes)."""
    payout = await use_case.execute(
        tenant_id=identity.tenant_id,
        waiter_id=body.waiter_id,
        amount=body.amount,
        method=body.method.value,
    )
    return TipPayoutResponse(
        id=payout.id,
        waiter_id=payout.waiter_id,
        amount=payout.amount,
        currency=payout.currency,
        method=payout.method,
    )
