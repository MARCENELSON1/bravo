from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.invoice.value_objects import (
    Concept,
    DocType,
    InvoiceStatus,
    InvoiceType,
)
from app.domain.shared.money import Money


@dataclass(frozen=True)
class VatItem:
    """Un tramo de IVA. ``rate`` en puntos básicos (2100 = 21%); ``base`` (neto
    gravado) e ``amount`` (IVA) en unidad mínima."""

    rate: int
    base: Money
    amount: Money


@dataclass
class Invoice:
    """Comprobante fiscal, scopeado al tenant. ``order_id`` set cuando factura
    una comanda. ``number``/``cae`` se completan al autorizar (AFIP)."""

    id: str
    tenant_id: str
    type: InvoiceType
    point_of_sale: int
    doc_type: DocType
    doc_number: str
    concept: Concept
    net: Money
    vat: Money
    total: Money
    vat_items: list[VatItem] = field(default_factory=list)
    status: InvoiceStatus = InvoiceStatus.DRAFT
    order_id: str | None = None
    number: int | None = None
    cae: str | None = None
    cae_expiration: date | None = None
    rejection: str | None = None
    issued_at: datetime | None = None
    created_at: datetime | None = None

    def authorize(self, *, number: int, cae: str, cae_expiration: date) -> None:
        self.number = number
        self.cae = cae
        self.cae_expiration = cae_expiration
        self.status = InvoiceStatus.AUTHORIZED

    def reject(self, reason: str) -> None:
        self.status = InvoiceStatus.REJECTED
        self.rejection = reason
