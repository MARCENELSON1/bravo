"""Pure tax math (no I/O): back out IVA from an IVA-included total and pick the
comprobante type. Integer minor units throughout (AFIP validates
``ImpTotal = ImpNeto + ImpIVA``)."""

from __future__ import annotations

from app.domain.invoice.entities import VatItem
from app.domain.invoice.value_objects import (
    VAT_0,
    VAT_21,
    DocType,
    FiscalCondition,
    InvoiceType,
)
from app.domain.shared.money import Money


def split_vat(total: Money, rate_bp: int = VAT_21) -> tuple[Money, Money, list[VatItem]]:
    """From an IVA-included total → (neto, IVA, [VatItem])."""
    net_amount = round(total.amount * 10000 / (10000 + rate_bp))
    net = Money(net_amount, total.currency)
    vat = Money(total.amount - net_amount, total.currency)
    return net, vat, [VatItem(rate=rate_bp, base=net, amount=vat)]


def no_vat(total: Money) -> tuple[Money, Money, list[VatItem]]:
    """Comprobante C (monotributo): el total no discrimina IVA."""
    zero = Money.zero(total.currency)
    return total, zero, [VatItem(rate=VAT_0, base=total, amount=zero)]


def invoice_type_for(emitter: FiscalCondition, receptor_doc: DocType) -> InvoiceType:
    """Emisor monotributo → C. Emisor RI → A si el receptor tiene CUIT, si no B."""
    if emitter is FiscalCondition.MONOTRIBUTO:
        return InvoiceType.FACTURA_C
    if receptor_doc is DocType.CUIT:
        return InvoiceType.FACTURA_A
    return InvoiceType.FACTURA_B
