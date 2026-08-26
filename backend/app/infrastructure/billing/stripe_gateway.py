"""Adapter de Stripe para el billing del SaaS (Flujo A, región Internacional/USD).

Usa la API REST de Stripe vía httpx (form-encoded, auth Basic con la secret key).
El checkout es hosteado (Checkout Session en modo suscripción) con ``price_data``
inline — no hace falta pre-crear Prices en Stripe (optimización futura). La
metadata lleva ``tenant_id``/``subscription_id`` en la sesión Y en la suscripción
(``subscription_data[metadata]``) para resolver el tenant en los webhooks.

La verificación de firma del webhook es manual (HMAC-SHA256 sobre ``"{t}.{body}"``
con el ``whsec_…``, comparación constant-time + tolerancia de 5 min). ``transport``
y ``now`` son inyectables para testear sin red ni reloj real."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import Callable, Mapping

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

_STRIPE_BASE = "https://api.stripe.com"
_INTERVAL = {BillingInterval.MONTH: "month", BillingInterval.YEAR: "year"}
_SIGNATURE_TOLERANCE_S = 300  # 5 minutos (anti-replay)


class StripeBillingGateway(BillingGateway):
    def __init__(
        self,
        api_key: str,
        webhook_secret: str,
        *,
        base_url: str = _STRIPE_BASE,
        transport: httpx.AsyncBaseTransport | None = None,
        now: Callable[[], float] | None = None,
    ) -> None:
        self._api_key = api_key
        self._webhook_secret = webhook_secret
        self._base = base_url
        self._transport = transport
        self._now = now or time.time

    def _client(self) -> httpx.AsyncClient:
        # Stripe usa HTTP Basic con la secret key como usuario y password vacío.
        return httpx.AsyncClient(
            base_url=self._base,
            transport=self._transport,
            auth=(self._api_key, ""),
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
        trial_days: int = 0,
    ) -> CheckoutSession:
        data = {
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "line_items[0][quantity]": "1",
            "line_items[0][price_data][currency]": plan.price.currency.lower(),
            "line_items[0][price_data][unit_amount]": str(plan.price.amount),
            "line_items[0][price_data][recurring][interval]": _INTERVAL[plan.interval],
            "line_items[0][price_data][product_data][name]": f"Wellnod {plan.tier.value}",
            "metadata[tenant_id]": subscription.tenant_id,
            "metadata[subscription_id]": subscription.id,
            "subscription_data[metadata][tenant_id]": subscription.tenant_id,
            "subscription_data[metadata][subscription_id]": subscription.id,
        }
        if trial_days > 0:
            # Prueba con tarjeta upfront: Checkout pide el medio de pago por
            # default (no seteamos payment_method_collection=if_required, que lo
            # haría opcional); lo dejamos explícito en "always" para fijar la
            # intención. El primer cobro se difiere trial_days y al vencer Stripe
            # cobra el monto completo (webhook customer.subscription.updated=active).
            data["subscription_data[trial_period_days]"] = str(trial_days)
            data["payment_method_collection"] = "always"
        if payer_email:
            data["customer_email"] = payer_email
        async with self._client() as client:
            resp = await client.post("/v1/checkout/sessions", data=data)
            resp.raise_for_status()
            body = resp.json()
        return CheckoutSession(url=body["url"], external_ref=str(body["id"]))

    async def cancel(self, *, external_ref: str) -> None:
        async with self._client() as client:
            resp = await client.delete(f"/v1/subscriptions/{external_ref}")
        if resp.status_code == 404:
            return  # ya no existe → idempotente
        resp.raise_for_status()

    async def parse_webhook(
        self, *, payload: bytes, headers: Mapping[str, str]
    ) -> BillingEvent | None:
        if not self._verify(payload, headers.get("stripe-signature", "")):
            raise InvalidBillingWebhook()
        event = json.loads(payload)
        obj = (event.get("data") or {}).get("object") or {}
        etype = event.get("type")

        if etype == "checkout.session.completed":
            tenant_id = (obj.get("metadata") or {}).get("tenant_id")
            sub_id = obj.get("subscription")
            if tenant_id and sub_id:
                return BillingEvent(tenant_id, str(sub_id), BillingEventType.ACTIVATED)
            return None

        if etype in ("customer.subscription.updated", "customer.subscription.deleted"):
            tenant_id = (obj.get("metadata") or {}).get("tenant_id")
            sub_id = obj.get("id")
            if not (tenant_id and sub_id):
                return None
            if etype == "customer.subscription.deleted":
                return BillingEvent(tenant_id, str(sub_id), BillingEventType.CANCELED)
            status = obj.get("status")
            if status == "past_due":
                return BillingEvent(tenant_id, str(sub_id), BillingEventType.PAYMENT_FAILED)
            if status == "active":
                return BillingEvent(tenant_id, str(sub_id), BillingEventType.ACTIVATED)
            return None

        return None

    def _verify(self, payload: bytes, signature: str) -> bool:
        if not self._webhook_secret:
            return False
        parts = dict(p.split("=", 1) for p in signature.split(",") if "=" in p)
        timestamp, v1 = parts.get("t"), parts.get("v1")
        if not timestamp or not v1:
            return False
        try:
            if abs(self._now() - int(timestamp)) > _SIGNATURE_TOLERANCE_S:
                return False
        except ValueError:
            return False
        signed_payload = f"{timestamp}.".encode() + payload
        expected = hmac.new(
            self._webhook_secret.encode(), signed_payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, v1)
