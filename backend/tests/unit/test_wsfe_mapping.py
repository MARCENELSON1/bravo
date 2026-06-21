from __future__ import annotations

from app.domain.invoice.entities import Invoice
from app.domain.invoice.taxation import no_vat, split_vat
from app.domain.invoice.value_objects import (
    VAT_21,
    Concept,
    DocType,
    InvoiceType,
)
from app.domain.shared.money import Money
from app.infrastructure.invoicing.wsfe_mapping import (
    build_cae_request,
    cbte_tipo,
    doc_tipo,
    iva_id,
)


def _invoice(type_: InvoiceType, total: Money, *, c: bool = False) -> Invoice:
    net, vat, items = no_vat(total) if c else split_vat(total)
    return Invoice(
        id="1",
        tenant_id="t",
        type=type_,
        point_of_sale=1,
        doc_type=DocType.CONSUMIDOR_FINAL,
        doc_number="0",
        concept=Concept.PRODUCTOS,
        net=net,
        vat=vat,
        total=total,
        vat_items=items,
    )


def test_afip_codes() -> None:
    assert cbte_tipo(InvoiceType.FACTURA_A) == 1
    assert cbte_tipo(InvoiceType.FACTURA_B) == 6
    assert cbte_tipo(InvoiceType.FACTURA_C) == 11
    assert doc_tipo(DocType.CONSUMIDOR_FINAL) == 99
    assert doc_tipo(DocType.CUIT) == 80
    assert iva_id(VAT_21) == 5


def test_build_cae_request_b_discriminates_iva() -> None:
    det = build_cae_request(_invoice(InvoiceType.FACTURA_B, Money(300000, "ARS")), 5, "20260621")
    assert det["CbteDesde"] == 5 and det["CbteHasta"] == 5
    assert det["DocTipo"] == 99 and det["DocNro"] == 0
    assert det["ImpTotal"] == 3000.0
    assert det["ImpNeto"] == 2479.34
    assert det["ImpIVA"] == 520.66
    iva = det["Iva"]
    assert isinstance(iva, dict)
    assert iva["AlicIva"][0]["Id"] == 5


def test_build_cae_request_c_has_no_iva() -> None:
    invoice = _invoice(InvoiceType.FACTURA_C, Money(50000, "ARS"), c=True)
    det = build_cae_request(invoice, 1, "20260621")
    assert det["ImpIVA"] == 0.0
    assert "Iva" not in det  # monotributo no discrimina IVA
