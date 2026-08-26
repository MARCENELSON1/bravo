"""E2e de los endpoints de billing (Flujo A) con el resolver de pasarelas
overrideado por un fake — checkout/webhook sin tocar Stripe/MercadoPago real."""

from __future__ import annotations

from uuid import uuid4

import pytest_asyncio
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.domain.billing.entities import Plan
from app.domain.billing.ports import BillingGateway, BillingGatewayResolver
from app.domain.billing.value_objects import (
    BillingEvent,
    BillingEventType,
    BillingRail,
    BillingRegion,
    CheckoutSession,
    PlanTier,
)
from app.domain.shared.money import Money
from app.infrastructure.persistence.mappers import plan_to_orm
from tests.fakes import FakeEmailSender
from tests.integration.test_e2e_auth import _onboard_verify_login
from tests.integration.test_e2e_payments import _auth


class _FakeGateway(BillingGateway):
    def __init__(self) -> None:
        self.event: BillingEvent | None = None

    async def start_checkout(self, *, subscription, plan, success_url, cancel_url, payer_email=None, trial_days=0):  # noqa: ANN001, E501
        return CheckoutSession(url="https://pay/redirect", external_ref="ext-1")

    async def cancel(self, *, external_ref: str) -> None:
        pass

    async def parse_webhook(self, *, payload, headers):  # noqa: ANN001
        return self.event


class _FakeResolver(BillingGatewayResolver):
    def __init__(self, gateway: BillingGateway) -> None:
        self._gateway = gateway

    def for_rail(self, rail: BillingRail) -> BillingGateway:
        return self._gateway


@pytest_asyncio.fixture
async def billing_api(clean_tables: None):
    from app.main import create_app

    app = create_app()
    container = app.state.container
    fake_email = FakeEmailSender()
    gateway = _FakeGateway()
    container.email_sender.override(providers.Object(fake_email))
    container.billing_gateway_resolver.override(providers.Object(_FakeResolver(gateway)))
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as http:
            yield http, fake_email, container, gateway
    finally:
        container.email_sender.reset_override()
        container.billing_gateway_resolver.reset_override()
        await container.db().dispose()


async def _seed_plan(container) -> str:  # noqa: ANN001
    plan = Plan(
        id=str(uuid4()),
        tier=PlanTier.PRO,
        region=BillingRegion.INTL,
        price=Money(4900, "USD"),
        features=frozenset({"copilot"}),
    )
    async with container.db().session() as session:
        session.add(plan_to_orm(plan))
    return plan.id


async def test_subscription_starts_null_then_checkout_then_webhook_activates(
    billing_api, admin_engine: AsyncEngine
):
    http, fake_email, container, gateway = billing_api
    tokens = await _onboard_verify_login(http, fake_email, slug="biz", email="o@biz.com")
    h = _auth(tokens)
    plan_id = await _seed_plan(container)

    # Sin suscripción todavía.
    r = await http.get("/api/v1/billing/subscription", headers=h)
    assert r.status_code == 200, r.text
    assert r.json() is None

    # Los planes de la región se listan.
    plans = await http.get("/api/v1/billing/plans?region=INTL", headers=h)
    assert plans.status_code == 200
    assert [p["id"] for p in plans.json()] == [plan_id]
    assert plans.json()[0]["currency"] == "USD"

    # Checkout → URL de pago + suscripción INCOMPLETE.
    co = await http.post("/api/v1/billing/checkout", json={"plan_id": plan_id}, headers=h)
    assert co.status_code == 200, co.text
    assert co.json()["url"] == "https://pay/redirect"
    sub = (await http.get("/api/v1/billing/subscription", headers=h)).json()
    assert sub["status"] == "INCOMPLETE"
    assert sub["grants_access"] is False
    assert sub["rail"] == "STRIPE"

    # Webhook ACTIVATED → la suscripción pasa a ACTIVE.
    async with admin_engine.begin() as conn:
        tenant_id = str(
            (await conn.execute(text("SELECT id FROM tenants LIMIT 1"))).scalar_one()
        )
    gateway.event = BillingEvent(
        tenant_id=tenant_id, external_ref="sub_1", type=BillingEventType.ACTIVATED
    )
    wh = await http.post("/api/v1/billing/webhooks/stripe", content=b"{}")
    assert wh.status_code == 200, wh.text
    active = (await http.get("/api/v1/billing/subscription", headers=h)).json()
    assert active["status"] == "ACTIVE"
    assert active["grants_access"] is True


async def test_public_plans_listed_without_auth(billing_api):
    http, fake_email, container, gateway = billing_api
    await _seed_plan(container)  # PRO/INTL/USD 4900, active

    # Endpoint PÚBLICO: sin header de auth.
    r = await http.get("/api/v1/public/plans?region=INTL")
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data) == 1
    p = data[0]
    assert p == {"tier": "PRO", "amount": 4900, "currency": "USD", "interval": "MONTH"}
    # Proyección lean: no filtra id/region/features al público.
    assert "id" not in p and "features" not in p and "region" not in p

    # Otra región → vacío (cada landing ve solo su región).
    other = await http.get("/api/v1/public/plans?region=AR")
    assert other.status_code == 200
    assert other.json() == []


async def test_cancel_subscription(billing_api):
    http, fake_email, container, gateway = billing_api
    tokens = await _onboard_verify_login(http, fake_email, slug="biz2", email="o@biz2.com")
    h = _auth(tokens)
    plan_id = await _seed_plan(container)
    await http.post("/api/v1/billing/checkout", json={"plan_id": plan_id}, headers=h)

    dele = await http.delete("/api/v1/billing/subscription", headers=h)
    assert dele.status_code == 204, dele.text
    sub = (await http.get("/api/v1/billing/subscription", headers=h)).json()
    assert sub["status"] == "CANCELED"
