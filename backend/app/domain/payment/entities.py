from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

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
    category: str | None = None
    counterparty: str | None = None
    description: str | None = None
    external_ref: str | None = None
    created_at: datetime | None = None

    def confirm(self) -> None:
        self.status = PaymentStatus.CONFIRMED

    def fail(self) -> None:
        self.status = PaymentStatus.FAILED
