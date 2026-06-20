"""Unit tests for the MercadoPago adapter using an in-process httpx transport
(no network): preference creation, status mapping and signature validation."""

from __future__ import annotations

import hashlib
import hmac

import httpx

from app.domain.payment.entities import Payment
from app.domain.payment.value_objects import PaymentDirection, PaymentMethod, PaymentStatus
from app.domain.shared.money import Money
from app.infrastructure.payments.mercadopago_gateway import MercadoPagoGateway


def _payment(
    method: PaymentMethod = PaymentMethod.MERCADOPAGO,
    direction: PaymentDirection = PaymentDirection.INFLOW,
) -> Payment:
    return Payment(
        id="pay1",
        tenant_id="t1",
        direction=direction,
        amount=Money(300000, "ARS"),
        method=method,
        status=PaymentStatus.PENDING,
        order_id="o1",
    )


def _gateway(handler, *, secret: str = "s3cret", token: str = "TEST-abc") -> MercadoPagoGateway:
    return MercadoPagoGateway(
        access_token=token,
        webhook_secret=secret,
        notification_url="https://hook.example/api/v1/webhooks/mercadopago",
        transport=httpx.MockTransport(handler),
    )


async def test_charge_online_creates_preference_and_stays_pending() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["body"] = request.content.decode()
        return httpx.Response(
            201,
            json={
                "id": "pref-123",
                "init_point": "https://mp/checkout/prod",
                "sandbox_init_point": "https://mp/checkout/sandbox",
            },
        )

    payment = await _gateway(handler).charge(payment=_payment())

    assert payment.status is PaymentStatus.PENDING
    assert payment.external_ref == "pref-123"
    # TEST credentials → the sandbox checkout link is surfaced.
    assert payment.checkout_url == "https://mp/checkout/sandbox"
    assert captured["path"] == "/checkout/preferences"
    assert "t1:pay1" in captured["body"]  # external_reference routes the webhook
    assert "3000.0" in captured["body"]  # 300000 minor units / 100 = 3000.00 pesos


async def test_charge_cash_confirms_without_calling_mercadopago() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("cash must not hit MercadoPago")

    payment = await _gateway(handler).charge(payment=_payment(method=PaymentMethod.CASH))

    assert payment.status is PaymentStatus.CONFIRMED
    assert payment.checkout_url is None


async def test_charge_outflow_confirms_even_if_method_is_mercadopago() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("egresos do not go through MercadoPago here")

    payment = await _gateway(handler).charge(
        payment=_payment(direction=PaymentDirection.OUTFLOW, method=PaymentMethod.MERCADOPAGO)
    )

    assert payment.status is PaymentStatus.CONFIRMED


async def test_fetch_status_maps_approved_to_confirmed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/payments/mp-999"
        return httpx.Response(
            200,
            json={"id": "mp-999", "status": "approved", "external_reference": "t1:pay1"},
        )

    status = await _gateway(handler).fetch_status(gateway_payment_id="mp-999")

    assert status.status is PaymentStatus.CONFIRMED
    assert status.external_reference == "t1:pay1"
    assert status.gateway_payment_id == "mp-999"


async def test_fetch_status_maps_rejected_to_failed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"id": "mp-1", "status": "rejected", "external_reference": "t1:p"}
        )

    status = await _gateway(handler).fetch_status(gateway_payment_id="mp-1")
    assert status.status is PaymentStatus.FAILED


def test_verify_signature_roundtrip() -> None:
    gw = _gateway(lambda r: httpx.Response(200), secret="topsecret")
    ts, data_id, request_id = "1700000000", "12345", "req-1"
    manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
    good = hmac.new(b"topsecret", manifest.encode(), hashlib.sha256).hexdigest()

    assert gw.verify_signature(data_id=data_id, request_id=request_id, ts=ts, received_hmac=good)
    assert not gw.verify_signature(
        data_id=data_id, request_id=request_id, ts=ts, received_hmac="deadbeef"
    )


def test_verify_signature_rejects_when_secret_missing() -> None:
    gw = _gateway(lambda r: httpx.Response(200), secret="")
    assert not gw.verify_signature(data_id="1", request_id="r", ts="1", received_hmac="x")
