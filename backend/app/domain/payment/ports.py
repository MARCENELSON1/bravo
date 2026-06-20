from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.payment.entities import Payment
from app.domain.payment.value_objects import PaymentStatus


class PaymentGateway(ABC):
    """Port to initiate/confirm a charge.

    The MVP uses ``ManualPaymentGateway`` (the money already moved outside the
    system → confirms immediately). MercadoPago / QR / Payway adapters slot in
    behind this same port and may return PENDING until a webhook confirms.
    """

    @abstractmethod
    async def charge(self, *, payment: Payment) -> Payment: ...


@dataclass(frozen=True)
class GatewayChargeStatus:
    """Normalised view of a charge as reported by the gateway (via webhook
    polling). ``external_reference`` is the value we sent when creating the
    charge (``"<tenant_id>:<payment_id>"``) so the notification can be routed
    back to the right tenant and payment without a user token."""

    gateway_payment_id: str
    external_reference: str | None
    status: PaymentStatus


class PaymentNotificationGateway(ABC):
    """Port for inbound gateway notifications (webhooks).

    Implemented only by online gateways (MercadoPago). ``verify_signature``
    authenticates the request (the endpoint is public); ``fetch_status`` asks
    the gateway for the authoritative status — notifications are not trusted at
    face value."""

    @abstractmethod
    def verify_signature(
        self,
        *,
        data_id: str | None,
        request_id: str | None,
        ts: str | None,
        received_hmac: str,
    ) -> bool: ...

    @abstractmethod
    async def fetch_status(self, *, gateway_payment_id: str) -> GatewayChargeStatus: ...
