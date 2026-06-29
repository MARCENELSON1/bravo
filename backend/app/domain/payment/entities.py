from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.payment.exceptions import PaymentNotRefundable
from app.domain.payment.value_objects import PaymentDirection, PaymentMethod, PaymentStatus
from app.domain.shared.money import Money


@dataclass
class Payment:
    """A money movement, scoped to a tenant.

    INFLOW = cobro de una comanda (``order_id`` set). OUTFLOW = egreso/gasto
    (``order_id`` None; puede llevar rubro/contraparte). El ``external_ref`` es
    el id de la pasarela (MercadoPago) cuando aplica.
    """

    id: str
    tenant_id: str
    direction: PaymentDirection
    amount: Money
    method: PaymentMethod
    status: PaymentStatus = PaymentStatus.CONFIRMED
    order_id: str | None = None
    # Propina cobrada encima del ``amount`` (minor units, misma moneda). No es
    # ingreso del local: no entra en sale_facts, solo en el arqueo de caja.
    tip_amount: int = 0
    category: str | None = None
    counterparty: str | None = None
    description: str | None = None
    external_ref: str | None = None
    created_at: datetime | None = None
    # Transient gateway artifacts (NOT persisted): online gateways set these so
    # the caller can redirect the payer to a checkout link / render a QR. They
    # stay None for already-collected payments (cash/card/transfer).
    checkout_url: str | None = None
    qr_data: str | None = None

    def confirm(self) -> None:
        self.status = PaymentStatus.CONFIRMED

    def fail(self) -> None:
        self.status = PaymentStatus.FAILED

    def refund(self) -> None:
        """Reverse a confirmed payment (anular/reembolsar). Money-only: the arqueo
        excludes REFUNDED, so the collected total drops; the sale projection is
        untouched (undoing the sale is the reopen flow, separate)."""
        if self.status is not PaymentStatus.CONFIRMED:
            raise PaymentNotRefundable()
        self.status = PaymentStatus.REFUNDED
