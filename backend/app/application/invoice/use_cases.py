from __future__ import annotations

from uuid import uuid4

from app.domain.identity.ports import TenantContext
from app.domain.invoice.credentials_repository import TaxCredentialRepository
from app.domain.invoice.entities import Invoice
from app.domain.invoice.exceptions import OrderNotInvoiceable, TaxGatewayNotConnected
from app.domain.invoice.ports import ElectronicInvoicing
from app.domain.invoice.repository import InvoiceRepository
from app.domain.invoice.taxation import invoice_type_for, no_vat, split_vat
from app.domain.invoice.value_objects import Concept, DocType, InvoiceStatus, InvoiceType
from app.domain.order.exceptions import OrderNotFound
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import OrderStatus


class IssueInvoice:
    """Factura una comanda pagada: deriva el tipo (según condición del emisor +
    receptor), calcula neto/IVA, pide el CAE y persiste el comprobante."""

    def __init__(
        self,
        invoices: InvoiceRepository,
        orders: OrderRepository,
        tax_credentials: TaxCredentialRepository,
        invoicing: ElectronicInvoicing,
        tenant_context: TenantContext,
    ) -> None:
        self._invoices = invoices
        self._orders = orders
        self._tax_credentials = tax_credentials
        self._invoicing = invoicing
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, order_id: str, doc_type: str, doc_number: str
    ) -> Invoice:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        if order.status is not OrderStatus.PAID:
            raise OrderNotInvoiceable()

        existing = await self._invoices.get_by_order(tenant_id, order_id)
        if existing is not None and existing.status is InvoiceStatus.AUTHORIZED:
            return existing  # idempotente: ya facturada

        credential = await self._tax_credentials.get_by_tenant(tenant_id)
        if credential is None:
            raise TaxGatewayNotConnected()

        receptor = DocType(doc_type)
        inv_type = invoice_type_for(credential.fiscal_condition, receptor)
        total = order.total()
        if inv_type is InvoiceType.FACTURA_C:
            net, vat, vat_items = no_vat(total)
        else:
            net, vat, vat_items = split_vat(total)

        invoice = Invoice(
            id=str(uuid4()),
            tenant_id=tenant_id,
            type=inv_type,
            point_of_sale=credential.point_of_sale,
            doc_type=receptor,
            doc_number=doc_number,
            concept=Concept.PRODUCTOS,
            net=net,
            vat=vat,
            total=total,
            vat_items=vat_items,
            status=InvoiceStatus.DRAFT,
            order_id=order_id,
        )
        result = await self._invoicing.authorize(invoice=invoice)
        if (
            result.authorized
            and result.cae is not None
            and result.number is not None
            and result.cae_expiration is not None
        ):
            invoice.authorize(
                number=result.number, cae=result.cae, cae_expiration=result.cae_expiration
            )
        else:
            invoice.reject(result.observations or "Rechazado por AFIP")
        await self._invoices.add(invoice)
        return invoice


class ListInvoices:
    def __init__(self, invoices: InvoiceRepository, tenant_context: TenantContext) -> None:
        self._invoices = invoices
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> list[Invoice]:
        self._tenant_context.set(tenant_id)
        return await self._invoices.list(tenant_id)


class GetOrderInvoice:
    def __init__(self, invoices: InvoiceRepository, tenant_context: TenantContext) -> None:
        self._invoices = invoices
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, order_id: str) -> Invoice | None:
        self._tenant_context.set(tenant_id)
        return await self._invoices.get_by_order(tenant_id, order_id)
