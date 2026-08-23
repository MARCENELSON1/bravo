from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status

from app.application.customer.use_cases import (
    CreateCustomer,
    DeleteCustomer,
    GetCustomer,
    GetCustomerHistory,
    GetCustomerStats,
    ListCustomers,
    UpdateCustomer,
)
from app.container import Container
from app.domain.customer.entities import Customer
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.customers import (
    CustomerHistoryResponse,
    CustomerRequest,
    CustomerResponse,
    CustomerStatsResponse,
    CustomerStatsRowResponse,
)

router = APIRouter(prefix="/customers", tags=["customers"])

# Ver clientes: roles de salón; gestionarlos: management.
_VIEW_ROLES = (Role.OWNER, Role.MANAGER, Role.WAITER, Role.CASHIER)
_MANAGE_ROLES = (Role.OWNER, Role.MANAGER)


def _response(customer: Customer) -> CustomerResponse:
    return CustomerResponse(
        id=customer.id,
        name=customer.name,
        phone=customer.phone,
        email=customer.email,
        notes=customer.notes,
        no_contactar=customer.no_contactar,
    )


@router.get("", response_model=list[CustomerResponse])
@inject
async def list_customers(
    search: str | None = Query(default=None, max_length=120),
    identity: AccessClaims = Depends(require_roles(*_VIEW_ROLES)),
    use_case: ListCustomers = Depends(Provide[Container.list_customers]),
) -> list[CustomerResponse]:
    rows = await use_case.execute(tenant_id=identity.tenant_id, search=search)
    return [_response(c) for c in rows]


# /stats va ANTES de /{customer_id} — si no, "stats" matchea como customer_id.
@router.get("/stats", response_model=CustomerStatsResponse)
@inject
async def customer_stats(
    identity: AccessClaims = Depends(require_roles(*_VIEW_ROLES)),
    use_case: GetCustomerStats = Depends(Provide[Container.get_customer_stats]),
) -> CustomerStatsResponse:
    """Agregados de compra por cliente (para segmentar): visitas, total gastado,
    primera y última visita — solo sobre comandas atribuidas (nada inferido)."""
    report = await use_case.execute(tenant_id=identity.tenant_id)
    return CustomerStatsResponse(
        currency=report.currency,
        rows=[
            CustomerStatsRowResponse(
                customer_id=r.customer_id,
                name=r.name,
                phone=r.phone,
                visits=r.visits,
                total_spent=r.total_spent,
                first_visit_at=r.first_visit_at.isoformat() if r.first_visit_at else None,
                last_visit_at=r.last_visit_at.isoformat() if r.last_visit_at else None,
            )
            for r in report.rows
        ],
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
@inject
async def get_customer(
    customer_id: str,
    identity: AccessClaims = Depends(require_roles(*_VIEW_ROLES)),
    use_case: GetCustomer = Depends(Provide[Container.get_customer]),
) -> CustomerResponse:
    return _response(
        await use_case.execute(tenant_id=identity.tenant_id, customer_id=customer_id)
    )


@router.get("/{customer_id}/history", response_model=CustomerHistoryResponse)
@inject
async def customer_history(
    customer_id: str,
    identity: AccessClaims = Depends(require_roles(*_VIEW_ROLES)),
    use_case: GetCustomerHistory = Depends(Provide[Container.get_customer_history]),
) -> CustomerHistoryResponse:
    """Historial de compras del cliente: visitas + total gastado + última visita,
    solo sobre comandas explícitamente atribuidas (nada inferido)."""
    h = await use_case.execute(tenant_id=identity.tenant_id, customer_id=customer_id)
    return CustomerHistoryResponse(
        customer_id=h.customer_id,
        currency=h.currency,
        visits=h.visits,
        total_spent=h.total_spent,
        last_visit_at=h.last_visit_at.isoformat() if h.last_visit_at else None,
    )


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_customer(
    body: CustomerRequest,
    identity: AccessClaims = Depends(require_roles(*_MANAGE_ROLES)),
    use_case: CreateCustomer = Depends(Provide[Container.create_customer]),
) -> CustomerResponse:
    customer = await use_case.execute(
        tenant_id=identity.tenant_id,
        name=body.name,
        phone=body.phone,
        email=body.email,
        notes=body.notes,
        no_contactar=body.no_contactar,
    )
    return _response(customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
@inject
async def update_customer(
    customer_id: str,
    body: CustomerRequest,
    identity: AccessClaims = Depends(require_roles(*_MANAGE_ROLES)),
    use_case: UpdateCustomer = Depends(Provide[Container.update_customer]),
) -> CustomerResponse:
    customer = await use_case.execute(
        tenant_id=identity.tenant_id,
        customer_id=customer_id,
        name=body.name,
        phone=body.phone,
        email=body.email,
        notes=body.notes,
        no_contactar=body.no_contactar,
    )
    return _response(customer)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_customer(
    customer_id: str,
    identity: AccessClaims = Depends(require_roles(*_MANAGE_ROLES)),
    use_case: DeleteCustomer = Depends(Provide[Container.delete_customer]),
) -> None:
    await use_case.execute(tenant_id=identity.tenant_id, customer_id=customer_id)
