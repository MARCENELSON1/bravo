from __future__ import annotations

import hashlib
import hmac
import json

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
from app.infrastructure.billing.mercadopago_gateway import MercadoPagoPreapprovalGateway
from app.infrastructure.billing.resolver import RailBillingGatewayResolver
from app.infrastructure.billing.stripe_gateway import StripeBillingGateway

_SECRET = "mpsecret"


def _plan() -> Plan:
    return Plan(id="plan1", tier=PlanTier.PRO, region=BillingRegion.AR, price=Money(500000, "ARS"))


def _sub() -> Subscription:
    return Subscription(
        id="s1",
        tenant_id="t1",
        plan_id="plan1",
        region=BillingRegion.AR,
        rail=BillingRail.MERCADOPAGO,
    )


def _gw(transport: httpx.MockTransport) -> MercadoPagoPreapprovalGateway:
    return MercadoPagoPreapprovalGateway("mp-token", _SECRET, transport=transport)


def _headers(
    data_id: str, *, req_id: str = "req-1", ts: str = "123", secret: str = _SECRET
) -> dict:
    manifest = f"id:{data_id};request-id:{req_id};ts:{ts};"
    sig = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return {"x-signature": f"ts={ts},v1={sig}", "x-request-id": req_id}


# --- checkout ---------------------------------------------------------------


async def test_start_checkout_creates_preapproval():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "pre_1", "init_point": "https://mp/x"})

    result = await _gw(httpx.MockTransport(handler)).start_checkout(
        subscription=_sub(),
        plan=_plan(),
        success_url="https://ok",
        cancel_url="https://no",
        payer_email="dueño@bar.com",
    )
    assert result.url == "https://mp/x"
    assert result.external_ref == "pre_1"
    assert captured["url"].endswith("/preapproval")
    body = captured["body"]
    assert body["external_reference"] == "t1:s1"
    assert body["payer_email"] == "dueño@bar.com"
    assert body["auto_recurring"]["transaction_amount"] == 5000.0  # 500000 centavos → 5000 pesos
    assert body["auto_recurring"]["currency_id"] == "ARS"
    assert body["auto_recurring"]["frequency_type"] == "months"
    # Sin trial_days no se manda free_trial.
    assert "free_trial" not in body["auto_recurring"]


async def test_start_checkout_with_trial_adds_free_trial():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "pre_1", "init_point": "https://mp/x"})

    await _gw(httpx.MockTransport(handler)).start_checkout(
        subscription=_sub(),
        plan=_plan(),
        success_url="https://ok",
        cancel_url="https://no",
        payer_email="dueño@bar.com",
        trial_days=30,
    )
    free_trial = captured["body"]["auto_recurring"]["free_trial"]
    assert free_trial == {"frequency": 30, "frequency_type": "days"}


async def test_start_checkout_requires_payer_email():
    with pytest.raises(ValueError, match="payer_email"):
        await _gw(httpx.MockTransport(lambda r: httpx.Response(200))).start_checkout(
            subscription=_sub(), plan=_plan(), success_url="s", cancel_url="c"
        )


async def test_cancel_puts_cancelled():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PUT"
        assert str(request.url).endswith("/preapproval/pre_9")
        assert json.loads(request.content) == {"status": "cancelled"}
        return httpx.Response(200, json={"id": "pre_9", "status": "cancelled"})

    await _gw(httpx.MockTransport(handler)).cancel(external_ref="pre_9")


# --- webhooks ---------------------------------------------------------------


def _webhook_transport(status: str):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url).endswith("/preapproval/pre_1")
        return httpx.Response(
            200, json={"id": "pre_1", "status": status, "external_reference": "t1:s1"}
        )

    return httpx.MockTransport(handler)


async def test_webhook_authorized_activates():
    payload = json.dumps({"type": "subscription_preapproval", "data": {"id": "pre_1"}}).encode()
    event = await _gw(_webhook_transport("authorized")).parse_webhook(
        payload=payload, headers=_headers("pre_1")
    )
    assert event is not None
    assert event.tenant_id == "t1"
    assert event.external_ref == "pre_1"
    assert event.type is BillingEventType.ACTIVATED


async def test_webhook_paused_is_payment_failed():
    payload = json.dumps({"type": "subscription_preapproval", "data": {"id": "pre_1"}}).encode()
    event = await _gw(_webhook_transport("paused")).parse_webhook(
        payload=payload, headers=_headers("pre_1")
    )
    assert event.type is BillingEventType.PAYMENT_FAILED


async def test_webhook_bad_signature_raises():
    payload = json.dumps({"type": "subscription_preapproval", "data": {"id": "pre_1"}}).encode()
    bad = {"x-signature": "ts=123,v1=deadbeef", "x-request-id": "req-1"}
    with pytest.raises(InvalidBillingWebhook):
        await _gw(_webhook_transport("authorized")).parse_webhook(payload=payload, headers=bad)


async def test_webhook_non_preapproval_ignored():
    payload = json.dumps({"type": "payment", "data": {"id": "pre_1"}}).encode()
    # Firma válida pero topic que no es preapproval → None (ni siquiera consulta).
    event = await _gw(
        httpx.MockTransport(lambda r: httpx.Response(500))
    ).parse_webhook(payload=payload, headers=_headers("pre_1"))
    assert event is None


# --- resolver por riel -------------------------------------------------------


def test_resolver_maps_rail_to_gateway():
    stripe = StripeBillingGateway("sk", "whsec")
    mp = MercadoPagoPreapprovalGateway("tok", "sec")
    resolver = RailBillingGatewayResolver(stripe=stripe, mercadopago=mp)
    assert resolver.for_rail(BillingRail.STRIPE) is stripe
    assert resolver.for_rail(BillingRail.MERCADOPAGO) is mp
