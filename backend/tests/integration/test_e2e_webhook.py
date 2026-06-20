"""End-to-end online charge → MercadoPago webhook → order PAID, over HTTP + DB.

The external gateway is faked (no network): charging an online inflow leaves the
payment PENDING with a checkout link, and the webhook drives it to CONFIRMED and
settles the order. Signature verification and idempotency are exercised too.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient

from app.domain.payment.entities import Payment
from app.domain.payment.ports import (
    GatewayChargeStatus,
    PaymentGateway,
    PaymentNotificationGateway,
)
from app.domain.payment.value_objects import PaymentDirection, PaymentMethod, PaymentStatus
from tests.fakes import FakeEmailSender
from tests.integration.test_e2e_auth import _onboard_verify_login
from tests.integration.test_e2e_payments import _auth, _make_order


class FakeOnlineGateway(PaymentGateway, PaymentNotificationGateway):
    """Stands in for MercadoPago: online inflows stay PENDING with a link; the
    webhook later confirms them. ``valid_signature`` toggles the auth path."""

    def __init__(self) -> None:
        self.last_ref: str | None = None
        self.valid_signature = True

    async def charge(self, *, payment: Payment) -> Payment:
        online = (PaymentMethod.MERCADOPAGO, PaymentMethod.QR)
        if payment.direction is PaymentDirection.OUTFLOW or payment.method not in online:
            payment.confirm()
            return payment
        payment.external_ref = f"pref-{payment.id}"
        payment.checkout_url = f"https://mp.test/checkout/{payment.id}"
        self.last_ref = f"{payment.tenant_id}:{payment.id}"
        return payment

    def verify_signature(self, *, data_id, request_id, ts, received_hmac) -> bool:
        return self.valid_signature

    async def fetch_status(self, *, gateway_payment_id: str) -> GatewayChargeStatus:
        return GatewayChargeStatus(
            gateway_payment_id=gateway_payment_id,
            external_reference=self.last_ref,
            status=PaymentStatus.CONFIRMED,
        )


@pytest_asyncio.fixture
async def mp_client(
    clean_tables: None,
) -> AsyncIterator[tuple[AsyncClient, FakeEmailSender, FakeOnlineGateway]]:
    from app.main import create_app

    app = create_app()
    container = app.state.container
    fake_email = FakeEmailSender()
    gateway = FakeOnlineGateway()
    container.email_sender.override(providers.Object(fake_email))
    container.payment_gateway.override(providers.Object(gateway))
    container.mercadopago_gateway.override(providers.Object(gateway))
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as http:
            yield http, fake_email, gateway
    finally:
        container.email_sender.reset_override()
        container.payment_gateway.reset_override()
        container.mercadopago_gateway.reset_override()
        await container.db().dispose()


_HOOK = "/api/v1/webhooks/mercadopago?data.id=mp-1&type=payment"
_SIG = {"x-signature": "ts=1700000000,v1=abc", "x-request-id": "req-1"}


async def test_online_charge_pending_then_webhook_marks_paid(mp_client) -> None:
    http, fake_email, _ = mp_client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    order_id = await _make_order(http, h)  # total 300000

    charge = await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "MERCADOPAGO", "amount": 300000},
        headers=h,
    )
    assert charge.status_code == 201, charge.text
    assert charge.json()["status"] == "PENDING"
    assert charge.json()["checkout_url"]
    assert (await http.get(f"/api/v1/orders/{order_id}", headers=h)).json()["status"] != "PAID"

    hook = await http.post(_HOOK, headers=_SIG)
    assert hook.status_code == 200, hook.text
    assert (await http.get(f"/api/v1/orders/{order_id}", headers=h)).json()["status"] == "PAID"

    # Idempotent: replaying the same notification is a safe no-op.
    again = await http.post(_HOOK, headers=_SIG)
    assert again.status_code == 200
    assert (await http.get(f"/api/v1/orders/{order_id}", headers=h)).json()["status"] == "PAID"


async def test_webhook_rejects_invalid_signature(mp_client) -> None:
    http, fake_email, gateway = mp_client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    order_id = await _make_order(http, h)
    await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "MERCADOPAGO", "amount": 300000},
        headers=h,
    )

    gateway.valid_signature = False
    hook = await http.post(_HOOK, headers=_SIG)
    assert hook.status_code == 401
    assert (await http.get(f"/api/v1/orders/{order_id}", headers=h)).json()["status"] != "PAID"
