from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.payment.use_cases import ListExpenses, RegisterExpense
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.api.v1.payments import payment_to_response
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.payments import PaymentResponse, RegisterExpenseRequest

router = APIRouter(prefix="/expenses", tags=["expenses"])

_EXPENSE_ROLES = (Role.MANAGER, Role.OWNER)


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
@inject
async def register_expense(
    body: RegisterExpenseRequest,
    identity: AccessClaims = Depends(require_roles(*_EXPENSE_ROLES)),
    use_case: RegisterExpense = Depends(Provide[Container.register_expense]),
) -> PaymentResponse:
    payment = await use_case.execute(
        tenant_id=identity.tenant_id,
        method=body.method.value,
        amount=body.amount,
        category=body.category,
        counterparty=body.counterparty,
        description=body.description,
    )
    return payment_to_response(payment)


@router.get("", response_model=list[PaymentResponse])
@inject
async def list_expenses(
    identity: AccessClaims = Depends(current_identity),
    use_case: ListExpenses = Depends(Provide[Container.list_expenses]),
) -> list[PaymentResponse]:
    expenses = await use_case.execute(tenant_id=identity.tenant_id)
    return [payment_to_response(p) for p in expenses]
