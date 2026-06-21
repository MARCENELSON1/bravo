"""Pure mapping between our domain and the WSFEv1 contract (códigos AFIP). Kept
separate from the SOAP/CMS I/O so it can be unit-tested without AFIP."""

from __future__ import annotations

from app.domain.invoice.entities import Invoice
from app.domain.invoice.value_objects import (
    VAT_0,
    VAT_21,
    VAT_27,
    VAT_105,
    Concept,
    DocType,
    InvoiceType,
)

# Tipo de comprobante (FECAEReq.CbteTipo).
_CBTE_TIPO: dict[InvoiceType, int] = {
    InvoiceType.FACTURA_A: 1,
    InvoiceType.NOTA_DEBITO_A: 2,
    InvoiceType.NOTA_CREDITO_A: 3,
    InvoiceType.FACTURA_B: 6,
    InvoiceType.NOTA_DEBITO_B: 7,
    InvoiceType.NOTA_CREDITO_B: 8,
    InvoiceType.FACTURA_C: 11,
    InvoiceType.NOTA_DEBITO_C: 12,
    InvoiceType.NOTA_CREDITO_C: 13,
}
# Tipo de documento del receptor (DocTipo).
_DOC_TIPO: dict[DocType, int] = {
    DocType.CUIT: 80,
    DocType.CUIL: 86,
    DocType.DNI: 96,
    DocType.CONSUMIDOR_FINAL: 99,
}
# Id de alícuota de IVA (AlicIva.Id).
_IVA_ID: dict[int, int] = {VAT_0: 3, VAT_105: 4, VAT_21: 5, VAT_27: 6}
# Concepto (productos/servicios/ambos).
_CONCEPTO: dict[Concept, int] = {Concept.PRODUCTOS: 1, Concept.SERVICIOS: 2, Concept.AMBOS: 3}

_TYPES_C = (InvoiceType.FACTURA_C, InvoiceType.NOTA_DEBITO_C, InvoiceType.NOTA_CREDITO_C)


def cbte_tipo(invoice_type: InvoiceType) -> int:
    return _CBTE_TIPO[invoice_type]


def doc_tipo(doc_type: DocType) -> int:
    return _DOC_TIPO[doc_type]


def iva_id(rate_bp: int) -> int:
    return _IVA_ID[rate_bp]


def _pesos(minor: int) -> float:
    """Minor units (centavos) → pesos float con 2 decimales (boundary AFIP)."""
    return round(minor / 100, 2)


def build_cae_request(invoice: Invoice, number: int, cbte_fch: str) -> dict[str, object]:
    """FECAEDetRequest para ``FECAESolicitar``. ``cbte_fch`` = 'yyyymmdd'.
    Monotributo (C) no discrimina IVA; A/B mandan ImpNeto+ImpIVA+Iva."""
    doc_nro = int(invoice.doc_number) if invoice.doc_number.isdigit() else 0
    det: dict[str, object] = {
        "Concepto": _CONCEPTO[invoice.concept],
        "DocTipo": doc_tipo(invoice.doc_type),
        "DocNro": doc_nro,
        "CbteDesde": number,
        "CbteHasta": number,
        "CbteFch": cbte_fch,
        "ImpTotal": _pesos(invoice.total.amount),
        "ImpTotConc": 0.0,
        "ImpNeto": _pesos(invoice.net.amount),
        "ImpOpEx": 0.0,
        "ImpIVA": _pesos(invoice.vat.amount),
        "ImpTrib": 0.0,
        "MonId": "PES",
        "MonCotiz": 1,
    }
    if invoice.type not in _TYPES_C and invoice.vat.amount > 0:
        det["Iva"] = {
            "AlicIva": [
                {
                    "Id": iva_id(item.rate),
                    "BaseImp": _pesos(item.base.amount),
                    "Importe": _pesos(item.amount.amount),
                }
                for item in invoice.vat_items
            ]
        }
    return det
