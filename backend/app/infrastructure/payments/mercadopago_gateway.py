"""MercadoPago adapter: Checkout Pro link/QR for online charges + webhook.

Implements two ports:
  * ``PaymentGateway.charge`` — for online methods (MERCADOPAGO/QR) it resolves
    the *tenant's own* access token (Fase 3.5, multi-tenant) and creates a
    Checkout Pro *preference*, returning the payment PENDING with the
    ``checkout_url``. Already-collected money (cash/card/transfer) and every
    egreso confirm immediately. If the tenant has not connected MercadoPago the
    resolver raises ``PaymentGatewayNotConnected``.
  * ``PaymentNotificationGateway`` — validates the ``x-signature`` HMAC and asks
    the Payments API for the authoritative status (notifications aren't trusted).

Money crosses the API boundary as a float in major units (pesos); inside the
domain it is always an integer in minor units. Credentials never get logged.
"""

from __future__ import annotations

import hashlib
import hmac

import httpx

from app.domain.payment.entities import Payment
from app.domain.payment.ports import (
    GatewayChargeStatus,
    PaymentCredentialsResolver,
    PaymentGateway,
    PaymentNotificationGateway,
)
from app.domain.payment.value_objects import PaymentDirection, PaymentMethod, PaymentStatus

_API_BASE = "https://api.mercadopago.com"
_ONLINE_METHODS = (PaymentMethod.MERCADOPAGO, PaymentMethod.QR)
_MINOR_UNIT = 100  # currencies at launch all use 2 decimals

# MercadoPago payment status → our domain status. Anything else stays PENDING.
_STATUS_MAP = {
    "approved": PaymentStatus.CONFIRMED,
    "authorized": PaymentStatus.CONFIRMED,
    "refunded": PaymentStatus.REFUNDED,
    "charged_back": PaymentStatus.REFUNDED,
    "rejected": PaymentStatus.FAILED,
    "cancelled": PaymentStatus.FAILED,
}


class MercadoPagoGateway(PaymentGateway, PaymentNotificationGateway):
    def __init__(
        self,
        credentials_resolver: PaymentCredentialsResolver,
        webhook_secret: str,
        notification_url: str = "",
        access_token: str = "",
        marketplace_fee: int = 0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._resolver = credentials_resolver
        self._webhook_secret = webhook_secret
        self._notification_url = notification_url
        # App-level token used by the webhook's fetch_status (transition; the
        # per-tenant webhook routing lands in the API/webhook tramo).
        self._fetch_token = access_token
        self._marketplace_fee = marketplace_fee
        self._transport = transport  # injectable for tests (httpx.MockTransport)

    def _client(self, access_token: str) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=_API_BASE,
            transport=self._transport,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )

    async def charge(self, *, payment: Payment) -> Payment:
        # Only online inflows go through MercadoPago; the rest are already settled.
        if payment.direction is PaymentDirection.OUTFLOW or payment.method not in _ONLINE_METHODS:
            payment.confirm()
            return payment

        creds = await self._resolver.for_tenant(payment.tenant_id)
        body: dict[str, object] = {
            "items": [
                {
                    "title": payment.description or "Cobro",
                    "quantity": 1,
                    "currency_id": payment.amount.currency,
                    "unit_price": payment.amount.amount / _MINOR_UNIT,
                }
            ],
            "external_reference": f"{payment.tenant_id}:{payment.id}",
        }
        if self._notification_url:
            body["notification_url"] = self._notification_url
        if self._marketplace_fee > 0:
            body["marketplace_fee"] = self._marketplace_fee / _MINOR_UNIT

        async with self._client(creds.access_token) as client:
            resp = await client.post("/checkout/preferences", json=body)
            resp.raise_for_status()
            data = resp.json()

        pref_id = data.get("id")
        payment.external_ref = str(pref_id) if pref_id is not None else None
        link = data.get("init_point") if creds.live_mode else data.get("sandbox_init_point")
        payment.checkout_url = link
        payment.qr_data = link
        return payment

    def verify_signature(
        self,
        *,
        data_id: str | None,
        request_id: str | None,
        ts: str | None,
        received_hmac: str,
    ) -> bool:
        if not self._webhook_secret or not received_hmac or ts is None:
            return False
        # Manifest template: id:<data.id>;request-id:<x-request-id>;ts:<ts>;
        # Absent parts are dropped. Alphanumeric ids are lowercased per the docs.
        parts: list[str] = []
        if data_id is not None:
            parts.append(f"id:{data_id.lower()};")
        if request_id is not None:
            parts.append(f"request-id:{request_id};")
        parts.append(f"ts:{ts};")
        manifest = "".join(parts)
        expected = hmac.new(
            self._webhook_secret.encode(), manifest.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, received_hmac)

    async def fetch_status(self, *, gateway_payment_id: str) -> GatewayChargeStatus:
        async with self._client(self._fetch_token) as client:
            resp = await client.get(f"/v1/payments/{gateway_payment_id}")
            resp.raise_for_status()
            data = resp.json()
        return GatewayChargeStatus(
            gateway_payment_id=str(data.get("id", gateway_payment_id)),
            external_reference=data.get("external_reference"),
            status=_STATUS_MAP.get(str(data.get("status", "")), PaymentStatus.PENDING),
        )
