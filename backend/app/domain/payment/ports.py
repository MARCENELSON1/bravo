from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.payment.entities import Payment


class PaymentGateway(ABC):
    """Port to initiate/confirm a charge.

    The MVP uses ``ManualPaymentGateway`` (the money already moved outside the
    system → confirms immediately). MercadoPago / QR / Payway adapters slot in
    behind this same port.
    """

    @abstractmethod
    async def charge(self, *, payment: Payment) -> Payment: ...
