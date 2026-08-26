"""Adapter de MercadoPago para el billing del SaaS (Flujo A, región AR/ARS).

Usa la API de **Preapproval** (suscripciones recurrentes) con NUESTRO access token
de MercadoPago (no el del tenant — esto es el cobro del SaaS, no los cobros del
local). MercadoPago maneja montos en unidades MAYORES (pesos, float) — distinto de
Stripe. El webhook manda una notificación de ``preapproval`` que hay que resolver
con un GET al preapproval para conocer su estado; el ``tenant_id`` viaja en el
``external_reference`` que seteamos al crearlo. Firma del webhook (x-signature):
HMAC-SHA256 sobre el manifest ``id:<data.id>;request-id:<x-request-id>;ts:<ts>;``.
``transport`` es inyectable para testear sin red."""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping

import httpx

from app.domain.billing.entities import Plan, Subscription
from app.domain.billing.exceptions import InvalidBillingWebhook
from app.domain.billing.ports import BillingGateway
from app.domain.billing.value_objects import (
    BillingEvent,
    BillingEventType,
    BillingInterval,
    CheckoutSession,
)

_MP_BASE = "https://api.mercadopago.com"
_FREQUENCY = {BillingInterval.MONTH: (1, "months"), BillingInterval.YEAR: (12, "months")}
_STATUS_MAP = {
    "authorized": BillingEventType.ACTIVATED,
    "cancelled": BillingEventType.CANCELED,
    "paused": BillingEventType.PAYMENT_FAILED,
}


class MercadoPagoPreapprovalGateway(BillingGateway):
    def __init__(
        self,
        access_token: str,
        webhook_secret: str,
        *,
        base_url: str = _MP_BASE,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._access_token = access_token
        self._webhook_secret = webhook_secret
        self._base = base_url
        self._transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base,
            transport=self._transport,
            headers={"Authorization": f"Bearer {self._access_token}"},
            timeout=20.0,
        )

    async def start_checkout(
        self,
        *,
        subscription: Subscription,
        plan: Plan,
        success_url: str,
        cancel_url: str,
        payer_email: str | None = None,
    ) -> CheckoutSession:
        if not payer_email:
            raise ValueError("payer_email es obligatorio para MercadoPago Preapproval")
        frequency, frequency_type = _FREQUENCY[plan.interval]
        body = {
            "reason": f"Wellnod {plan.tier.value}",
            "external_reference": f"{subscription.tenant_id}:{subscription.id}",
            "payer_email": payer_email,
            "back_url": success_url,
            "status": "pending",
            "auto_recurring": {
                "frequency": frequency,
                "frequency_type": frequency_type,
                # MercadoPago usa unidades mayores (pesos), no centavos.
                "transaction_amount": plan.price.amount / 100,
                "currency_id": plan.price.currency,
            },
        }
        async with self._client() as client:
            resp = await client.post("/preapproval", json=body)
            resp.raise_for_status()
            data = resp.json()
        return CheckoutSession(url=data["init_point"], external_ref=str(data["id"]))

    async def cancel(self, *, external_ref: str) -> None:
        async with self._client() as client:
            resp = await client.put(
                f"/preapproval/{external_ref}", json={"status": "cancelled"}
            )
        if resp.status_code == 404:
            return  # ya no existe → idempotente
        resp.raise_for_status()

    async def parse_webhook(
        self, *, payload: bytes, headers: Mapping[str, str]
    ) -> BillingEvent | None:
        body = json.loads(payload) if payload else {}
        data_id = str((body.get("data") or {}).get("id") or "")
        if not data_id:
            return None
        if not self._verify(headers, data_id):
            raise InvalidBillingWebhook()
        topic = str(body.get("type") or body.get("topic") or "")
        if "preapproval" not in topic:
            return None  # solo nos interesan las suscripciones

        preapproval = await self._get_preapproval(data_id)
        if preapproval is None:
            return None
        external_reference = str(preapproval.get("external_reference") or "")
        tenant_id = external_reference.split(":", 1)[0]
        mapped = _STATUS_MAP.get(preapproval.get("status"))
        if not tenant_id or mapped is None:
            return None
        return BillingEvent(tenant_id, str(preapproval.get("id") or data_id), mapped)

    async def _get_preapproval(self, preapproval_id: str) -> dict | None:
        async with self._client() as client:
            resp = await client.get(f"/preapproval/{preapproval_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def _verify(self, headers: Mapping[str, str], data_id: str) -> bool:
        if not self._webhook_secret:
            return False
        x_signature = headers.get("x-signature", "")
        request_id = headers.get("x-request-id", "")
        parts = dict(p.split("=", 1) for p in x_signature.split(",") if "=" in p)
        ts, v1 = parts.get("ts"), parts.get("v1")
        if not ts or not v1:
            return False
        manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
        expected = hmac.new(
            self._webhook_secret.encode(), manifest.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, v1)
