from __future__ import annotations

from datetime import date

from app.domain.invoice.entities import Invoice
from app.domain.invoice.taxation import invoice_type_for, no_vat, split_vat
from app.domain.invoice.value_objects import (
    VAT_21,
    Concept,
    DocType,
    FiscalCondition,
    InvoiceStatus,
    InvoiceType,
)
from app.domain.shared.money import Money


def test_split_vat_21() -> None:
    net, vat, items = split_vat(Money(121000, "ARS"))
    assert net.amount == 100000
    assert vat.amount == 21000
    assert net.amount + vat.amount == 121000  # AFIP: ImpTotal = ImpNeto + ImpIVA
    assert items[0].rate == VAT_21


def test_no_vat_for_monotributo() -> None:
    net, vat, _ = no_vat(Money(50000, "ARS"))
    assert net.amount == 50000
    assert vat.amount == 0


def test_invoice_type_derivation() -> None:
    ri = FiscalCondition.RESPONSABLE_INSCRIPTO
    mono = FiscalCondition.MONOTRIBUTO
    assert invoice_type_for(mono, DocType.CUIT) is InvoiceType.FACTURA_C
    assert invoice_type_for(ri, DocType.CUIT) is InvoiceType.FACTURA_A
    assert invoice_type_for(ri, DocType.CONSUMIDOR_FINAL) is InvoiceType.FACTURA_B


def test_invoice_authorize_and_reject() -> None:
    inv = Invoice(
        id="1",
        tenant_id="t1",
        type=InvoiceType.FACTURA_B,
        point_of_sale=1,
        doc_type=DocType.CONSUMIDOR_FINAL,
        doc_number="0",
        concept=Concept.PRODUCTOS,
        net=Money(100000, "ARS"),
        vat=Money(21000, "ARS"),
        total=Money(121000, "ARS"),
    )
    inv.authorize(number=5, cae="68000000000000", cae_expiration=date(2026, 1, 1))
    assert inv.status is InvoiceStatus.AUTHORIZED
    assert inv.number == 5 and inv.cae == "68000000000000"

    inv.reject("10016: punto de venta inexistente")
    assert inv.status is InvoiceStatus.REJECTED
    assert inv.rejection is not None
