"""Persistencia del billing (Flujo A): catálogo de planes (global) + suscripción
por tenant (RLS). Prueba ORM + mappers + migración 0044 + RLS end-to-end."""

from __future__ import annotations

from uuid import uuid4

import pytest_asyncio
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.context import reset_current_tenant, set_current_tenant
from app.domain.billing.entities import Plan, Subscription
from app.domain.billing.value_objects import (
    BillingRail,
    BillingRegion,
    PlanTier,
    SubscriptionStatus,
)
from app.domain.shared.money import Money
from app.infrastructure.persistence.mappers import plan_to_orm
from tests.fakes import FakeEmailSender
from tests.integration.test_e2e_auth import _onboard_verify_login


@pytest_asyncio.fixture
async def billing_app(clean_tables: None):
    """App real con el container expuesto (para usar los repos directamente)."""
    from app.main import create_app

    app = create_app()
    container = app.state.container
    fake_email = FakeEmailSender()
    container.email_sender.override(providers.Object(fake_email))
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as http:
            yield http, fake_email, container
    finally:
        container.email_sender.reset_override()
        await container.db().dispose()


async def test_billing_persistence_round_trip(billing_app, admin_engine: AsyncEngine):
    http, fake_email, container = billing_app
    await _onboard_verify_login(http, fake_email, slug="bill", email="o@bill.com")
    async with admin_engine.begin() as conn:
        tenant_id = str(
            (await conn.execute(text("SELECT id FROM tenants LIMIT 1"))).scalar_one()
        )

    # Catálogo global: mismo tier por región, cada uno en su moneda.
    ar = Plan(
        id=str(uuid4()),
        tier=PlanTier.PRO,
        region=BillingRegion.AR,
        price=Money(500000, "ARS"),
        features=frozenset({"copilot"}),
    )
    intl = Plan(
        id=str(uuid4()),
        tier=PlanTier.PRO,
        region=BillingRegion.INTL,
        price=Money(4900, "USD"),
        features=frozenset({"copilot"}),
    )
    async with container.db().session() as session:
        session.add(plan_to_orm(ar))
        session.add(plan_to_orm(intl))

    # PlanRepository (sin RLS): por región + por id, con round-trip de precio/features.
    plans_ar = await container.plan_repository().list_active(BillingRegion.AR)
    assert [p.id for p in plans_ar] == [ar.id]
    assert plans_ar[0].price == Money(500000, "ARS")
    assert plans_ar[0].features == frozenset({"copilot"})
    got_intl = await container.plan_repository().get_by_id(intl.id)
    assert got_intl is not None and got_intl.region is BillingRegion.INTL

    # SubscriptionRepository (RLS): add → get → transición → save → get.
    token = set_current_tenant(tenant_id)
    try:
        sub = Subscription(
            id=str(uuid4()),
            tenant_id=tenant_id,
            plan_id=intl.id,
            region=BillingRegion.INTL,
            rail=BillingRail.STRIPE,
        )
        await container.subscription_repository().add(sub)

        loaded = await container.subscription_repository().get_by_tenant(tenant_id)
        assert loaded is not None
        assert loaded.status is SubscriptionStatus.INCOMPLETE
        assert loaded.rail is BillingRail.STRIPE

        loaded.activate()
        await container.subscription_repository().save(loaded)

        again = await container.subscription_repository().get_by_tenant(tenant_id)
        assert again is not None
        assert again.status is SubscriptionStatus.ACTIVE
    finally:
        reset_current_tenant(token)
