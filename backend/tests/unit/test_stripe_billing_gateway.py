from __future__ import annotations

import hashlib
import hmac
import json
from urllib.parse import parse_qs

import httpx
import pytest

from app.domain.billing.entities import Plan, Subscription
from app.domain.billing.exceptions import InvalidBillingWebhook
from app.domain.billing.value_objects import (
    BillingEventType,
    BillingRail,
    BillingRegion,
    PlanTier,
)
from app.domain.shared.money import Money
from app.infrastructure.billing.stripe_gateway import StripeBillingGateway

_SECRET = "whsec_test"
_TS = 1000


def _plan() -> Plan:
    return Plan(id="plan1", tier=PlanTier.PRO, region=BillingRegion.INTL, price=Money(4900, "USD"))


def _sub() -> Subscription:
    return Subscription(
        id="s1",
        tenant_id="t1",
        plan_id="plan1",
        region=BillingRegion.INTL,
        rail=BillingRail.STRIPE,
    )


def _signed(payload: bytes, *, secret: str = _SECRET, ts: int = _TS) -> str:
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def _gateway(transport: httpx.MockTransport | None = None) -> StripeBillingGateway:
    return StripeBillingGateway(
        "sk_test", _SECRET, transport=transport, now=lambda: float(_TS)
    )


# --- checkout ---------------------------------------------------------------


async def test_start_checkout_posts_subscription_session():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["form"] = parse_qs(request.content.decode())
        return httpx.Response(200, json={"id": "cs_1", "url": "https://checkout/x"})

    result = await _gateway(httpx.MockTransport(handler)).start_checkout(
        subscription=_sub(), plan=_plan(), success_url="https://ok", cancel_url="https://no"
    )
    assert result.url == "https://checkout/x"
    assert result.external_ref == "cs_1"
    assert captured["url"].endswith("/v1/checkout/sessions")
    form = captured["form"]
    assert form["mode"] == ["subscription"]
    assert form["line_items[0][price_data][currency]"] == ["usd"]
    assert form["line_items[0][price_data][unit_amount]"] == ["4900"]
    assert form["line_items[0][price_data][recurring][interval]"] == ["month"]
    # La metadata lleva el tenant en la sesión Y en la suscripción (para webhooks).
    assert form["metadata[tenant_id]"] == ["t1"]
    assert form["subscription_data[metadata][tenant_id]"] == ["t1"]
    # Sin trial_days no se manda período de prueba.
    assert "subscription_data[trial_period_days]" not in form


async def test_start_checkout_with_trial_sets_trial_and_requires_card():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["form"] = parse_qs(request.content.decode())
        return httpx.Response(200, json={"id": "cs_1", "url": "https://checkout/x"})

    await _gateway(httpx.MockTransport(handler)).start_checkout(
        subscription=_sub(),
        plan=_plan(),
        success_url="https://ok",
        cancel_url="https://no",
        trial_days=30,
    )
    form = captured["form"]
    assert form["subscription_data[trial_period_days]"] == ["30"]
    # Tarjeta obligatoria upfront (no if_required).
    assert form["payment_method_collection"] == ["always"]


async def test_cancel_deletes_subscription():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert str(request.url).endswith("/v1/subscriptions/sub_9")
        return httpx.Response(200, json={"id": "sub_9", "status": "canceled"})

    await _gateway(httpx.MockTransport(handler)).cancel(external_ref="sub_9")


async def test_cancel_is_idempotent_on_404():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": {"message": "No such subscription"}})

    await _gateway(httpx.MockTransport(handler)).cancel(external_ref="sub_gone")  # no raise


# --- webhooks ---------------------------------------------------------------


async def test_webhook_checkout_completed_is_activated():
    payload = json.dumps(
        {
            "type": "checkout.session.completed",
            "data": {"object": {"metadata": {"tenant_id": "t1"}, "subscription": "sub_1"}},
        }
    ).encode()
    event = await _gateway().parse_webhook(
        payload=payload, headers={"stripe-signature": _signed(payload)}
    )
    assert event is not None
    assert event.tenant_id == "t1"
    assert event.external_ref == "sub_1"
    assert event.type is BillingEventType.ACTIVATED


async def test_webhook_subscription_past_due_is_payment_failed():
    obj = {"id": "sub_1", "status": "past_due", "metadata": {"tenant_id": "t1"}}
    payload = json.dumps(
        {"type": "customer.subscription.updated", "data": {"object": obj}}
    ).encode()
    event = await _gateway().parse_webhook(
        payload=payload, headers={"stripe-signature": _signed(payload)}
    )
    assert event.type is BillingEventType.PAYMENT_FAILED
    assert event.external_ref == "sub_1"


async def test_webhook_subscription_deleted_is_canceled():
    payload = json.dumps(
        {
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_1", "metadata": {"tenant_id": "t1"}}},
        }
    ).encode()
    event = await _gateway().parse_webhook(
        payload=payload, headers={"stripe-signature": _signed(payload)}
    )
    assert event.type is BillingEventType.CANCELED


async def test_webhook_bad_signature_raises():
    payload = b'{"type":"checkout.session.completed","data":{"object":{}}}'
    with pytest.raises(InvalidBillingWebhook):
        await _gateway().parse_webhook(
            payload=payload, headers={"stripe-signature": "t=1000,v1=deadbeef"}
        )


async def test_webhook_unknown_type_returns_none():
    payload = json.dumps({"type": "invoice.created", "data": {"object": {}}}).encode()
    result = await _gateway().parse_webhook(
        payload=payload, headers={"stripe-signature": _signed(payload)}
    )
    assert result is None
