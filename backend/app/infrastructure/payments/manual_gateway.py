from __future__ import annotations

from app.domain.payment.entities import Payment
from app.domain.payment.ports import PaymentGateway


class ManualPaymentGateway(PaymentGateway):
    """Dev/MVP transport: the money already moved outside the system (cash,
    bank transfer, a charge taken on another device), so the payment is
    confirmed immediately. MercadoPago/QR/Payway adapters slot in behind the
    same port and may return PENDING until a webhook confirms.
    """

    async def charge(self, *, payment: Payment) -> Payment:
        payment.confirm()
        return payment
