from __future__ import annotations

from app.domain.errors import DomainError


class InvoiceNotFound(DomainError):
    code = "invoice_not_found"
    message = "No encontramos el comprobante indicado."


class OrderNotInvoiceable(DomainError):
    code = "order_not_invoiceable"
    message = "La comanda tiene que estar pagada para facturarse."


class TaxGatewayNotConnected(DomainError):
    code = "tax_gateway_not_connected"
    message = "El local no tiene AFIP conectado. Conectalo en Integraciones."
