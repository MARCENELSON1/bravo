from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.invoice.use_cases import GetOrderInvoice, IssueInvoice, ListInvoices
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.invoice.entities import Invoice
from app.domain.invoice.exceptions import InvoiceNotFound
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.invoices import InvoiceResponse, IssueInvoiceRequest

router = APIRouter(tags=["invoices"])

_INVOICE_ROLES = (Role.OWNER, Role.MANAGER)


def invoice_to_response(invoice: Invoice) -> InvoiceResponse:
    return InvoiceResponse(
        id=invoice.id,
        type=invoice.type.value,
        point_of_sale=invoice.point_of_sale,
        number=invoice.number,
        doc_type=invoice.doc_type.value,
        doc_number=invoice.doc_number,
        net=invoice.net.amount,
        vat=invoice.vat.amount,
        total=invoice.total.amount,
        currency=invoice.total.currency,
        status=invoice.status.value,
        cae=invoice.cae,
        cae_expiration=invoice.cae_expiration.isoformat() if invoice.cae_expiration else None,
        order_id=invoice.order_id,
        rejection=invoice.rejection,
    )


@router.post(
    "/orders/{order_id}/invoice",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def issue_invoice(
    order_id: str,
    body: IssueInvoiceRequest,
    identity: AccessClaims = Depends(require_roles(*_INVOICE_ROLES)),
    use_case: IssueInvoice = Depends(Provide[Container.issue_invoice]),
) -> InvoiceResponse:
    invoice = await use_case.execute(
        tenant_id=identity.tenant_id,
        order_id=order_id,
        doc_type=body.doc_type.value,
        doc_number=body.doc_number,
    )
    return invoice_to_response(invoice)


@router.get("/orders/{order_id}/invoice", response_model=InvoiceResponse)
@inject
async def get_order_invoice(
    order_id: str,
    identity: AccessClaims = Depends(current_identity),
    use_case: GetOrderInvoice = Depends(Provide[Container.get_order_invoice]),
) -> InvoiceResponse:
    invoice = await use_case.execute(tenant_id=identity.tenant_id, order_id=order_id)
    if invoice is None:
        raise InvoiceNotFound()
    return invoice_to_response(invoice)


@router.get("/invoices", response_model=list[InvoiceResponse])
@inject
async def list_invoices(
    identity: AccessClaims = Depends(current_identity),
    use_case: ListInvoices = Depends(Provide[Container.list_invoices]),
) -> list[InvoiceResponse]:
    invoices = await use_case.execute(tenant_id=identity.tenant_id)
    return [invoice_to_response(i) for i in invoices]
