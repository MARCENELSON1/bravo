from __future__ import annotations

import pytest

from app.application.billing.use_cases import (
    CancelSubscription,
    HandleBillingWebhook,
    StartSubscriptionCheckout,
)
from app.domain.billing.entities import Plan, Subscription
from app.domain.billing.exceptions import (
    PlanNotFound,
    SubscriptionAlreadyActive,
    SubscriptionNotFound,
)
from app.domain.billing.ports import BillingGateway, BillingGatewayResolver
from app.domain.billing.value_objects import (
    BillingEvent,
    BillingEventType,
    BillingRail,
    BillingRegion,
    CheckoutSession,
    PlanTier,
    SubscriptionStatus,
)
from app.domain.shared.money import Money


def _plan(region: BillingRegion = BillingRegion.INTL) -> Plan:
    cur = "USD" if region is BillingRegion.INTL else "ARS"
    return Plan(id="plan1", tier=PlanTier.PRO, region=region, price=Money(4900, cur))


class _FakePlans:
    def __init__(self, plan: Plan | None) -> None:
        self._plan = plan

    async def list_active(self, region):  # noqa: ANN001
        return [self._plan] if self._plan else []

    async def get_by_id(self, plan_id: str):
        return self._plan if self._plan and self._plan.id == plan_id else None


class _FakeSubs:
    def __init__(self, sub: Subscription | None = None) -> None:
        self.sub = sub
        self.added: Subscription | None = None
        self.saved: Subscription | None = None

    async def get_by_tenant(self, tenant_id: str):
        return self.sub

    async def get_by_external_ref(self, external_ref: str):
        return self.sub

    async def add(self, subscription: Subscription) -> None:
        self.added = subscription
        self.sub = subscription

    async def save(self, subscription: Subscription) -> None:
        self.saved = subscription
        self.sub = subscription


class _FakeGateway(BillingGateway):
    def __init__(self, event: BillingEvent | None = None) -> None:
        self.event = event
        self.checkout_calls: list = []
        self.cancel_calls: list[str] = []

    async def start_checkout(  # noqa: ANN001
        self, *, subscription, plan, success_url, cancel_url, payer_email=None
    ):
        self.checkout_calls.append(subscription.rail)
        return CheckoutSession(url="https://pay/x", external_ref="ext-123")

    async def cancel(self, *, external_ref: str) -> None:
        self.cancel_calls.append(external_ref)

    async def parse_webhook(self, *, payload: bytes, headers):  # noqa: ANN001
        return self.event


class _FakeResolver(BillingGatewayResolver):
    def __init__(self, gateway: BillingGateway) -> None:
        self._gateway = gateway
        self.rails: list[BillingRail] = []

    def for_rail(self, rail: BillingRail) -> BillingGateway:
        self.rails.append(rail)
        return self._gateway


class _NoopCtx:
    def set(self, tenant_id: str) -> None:
        pass


def _sub(status: SubscriptionStatus, **kw) -> Subscription:
    base = dict(
        id="s1",
        tenant_id="t1",
        plan_id="plan1",
        region=BillingRegion.INTL,
        rail=BillingRail.STRIPE,
        status=status,
    )
    base.update(kw)
    return Subscription(**base)


# --- StartSubscriptionCheckout ----------------------------------------------


async def test_checkout_creates_incomplete_and_returns_url():
    subs = _FakeSubs()
    gw = _FakeGateway()
    uc = StartSubscriptionCheckout(_FakePlans(_plan()), subs, _FakeResolver(gw), _NoopCtx())
    url = await uc.execute(
        tenant_id="t1", plan_id="plan1", success_url="s", cancel_url="c"
    )
    assert url == "https://pay/x"
    assert subs.added is not None
    assert subs.added.status is SubscriptionStatus.INCOMPLETE
    assert subs.added.external_ref == "ext-123"
    assert subs.added.rail is BillingRail.STRIPE


async def test_checkout_ar_plan_uses_mercadopago_rail():
    gw = _FakeGateway()
    resolver = _FakeResolver(gw)
    subs = _FakeSubs()
    uc = StartSubscriptionCheckout(
        _FakePlans(_plan(BillingRegion.AR)), subs, resolver, _NoopCtx()
    )
    await uc.execute(tenant_id="t1", plan_id="plan1", success_url="s", cancel_url="c")
    # El riel (y la pasarela) los fija la región del plan: AR → MercadoPago.
    assert resolver.rails == [BillingRail.MERCADOPAGO]
    assert subs.added.rail is BillingRail.MERCADOPAGO


async def test_checkout_rejected_when_already_active():
    subs = _FakeSubs(_sub(SubscriptionStatus.ACTIVE))
    uc = StartSubscriptionCheckout(
        _FakePlans(_plan()), subs, _FakeResolver(_FakeGateway()), _NoopCtx()
    )
    with pytest.raises(SubscriptionAlreadyActive):
        await uc.execute(tenant_id="t1", plan_id="plan1", success_url="s", cancel_url="c")


async def test_checkout_replaces_canceled_subscription():
    canceled = _sub(SubscriptionStatus.CANCELED)
    subs = _FakeSubs(canceled)
    uc = StartSubscriptionCheckout(
        _FakePlans(_plan()), subs, _FakeResolver(_FakeGateway()), _NoopCtx()
    )
    await uc.execute(tenant_id="t1", plan_id="plan1", success_url="s", cancel_url="c")
    # Reusa la fila (mismo id) vía save, no add (unique por tenant).
    assert subs.added is None
    assert subs.saved is not None
    assert subs.saved.id == canceled.id
    assert subs.saved.status is SubscriptionStatus.INCOMPLETE


async def test_checkout_plan_not_found():
    uc = StartSubscriptionCheckout(
        _FakePlans(None), _FakeSubs(), _FakeResolver(_FakeGateway()), _NoopCtx()
    )
    with pytest.raises(PlanNotFound):
        await uc.execute(tenant_id="t1", plan_id="nope", success_url="s", cancel_url="c")


# --- CancelSubscription ------------------------------------------------------


async def test_cancel_calls_gateway_and_cancels():
    gw = _FakeGateway()
    subs = _FakeSubs(_sub(SubscriptionStatus.ACTIVE, external_ref="ext-9"))
    await CancelSubscription(subs, _FakeResolver(gw), _NoopCtx()).execute(tenant_id="t1")
    assert gw.cancel_calls == ["ext-9"]
    assert subs.saved.status is SubscriptionStatus.CANCELED


async def test_cancel_idempotent_when_already_canceled():
    gw = _FakeGateway()
    subs = _FakeSubs(_sub(SubscriptionStatus.CANCELED, external_ref="ext-9"))
    await CancelSubscription(subs, _FakeResolver(gw), _NoopCtx()).execute(tenant_id="t1")
    assert gw.cancel_calls == []  # no vuelve a llamar a la pasarela


async def test_cancel_not_found():
    with pytest.raises(SubscriptionNotFound):
        await CancelSubscription(_FakeSubs(), _FakeResolver(_FakeGateway()), _NoopCtx()).execute(
            tenant_id="t1"
        )


# --- HandleBillingWebhook (idempotente) -------------------------------------


def _handler(subs: _FakeSubs, event: BillingEvent | None):
    return HandleBillingWebhook(subs, _FakeResolver(_FakeGateway(event)), _NoopCtx())


async def test_webhook_activated_activates():
    subs = _FakeSubs(_sub(SubscriptionStatus.INCOMPLETE))
    event = BillingEvent(tenant_id="t1", external_ref="ext-1", type=BillingEventType.ACTIVATED)
    await _handler(subs, event).execute(rail=BillingRail.STRIPE, payload=b"{}", headers={})
    assert subs.saved.status is SubscriptionStatus.ACTIVE
    assert subs.saved.external_ref == "ext-1"


async def test_webhook_activated_is_idempotent():
    subs = _FakeSubs(_sub(SubscriptionStatus.ACTIVE, external_ref="ext-1"))
    event = BillingEvent(tenant_id="t1", external_ref="ext-1", type=BillingEventType.ACTIVATED)
    await _handler(subs, event).execute(rail=BillingRail.STRIPE, payload=b"{}", headers={})
    assert subs.saved is None  # sin cambios → no persiste


async def test_webhook_payment_failed_marks_past_due():
    subs = _FakeSubs(_sub(SubscriptionStatus.ACTIVE, external_ref="ext-1"))
    event = BillingEvent(
        tenant_id="t1", external_ref="ext-1", type=BillingEventType.PAYMENT_FAILED
    )
    await _handler(subs, event).execute(rail=BillingRail.STRIPE, payload=b"{}", headers={})
    assert subs.saved.status is SubscriptionStatus.PAST_DUE


async def test_webhook_canceled():
    subs = _FakeSubs(_sub(SubscriptionStatus.ACTIVE, external_ref="ext-1"))
    event = BillingEvent(tenant_id="t1", external_ref="ext-1", type=BillingEventType.CANCELED)
    await _handler(subs, event).execute(rail=BillingRail.STRIPE, payload=b"{}", headers={})
    assert subs.saved.status is SubscriptionStatus.CANCELED


async def test_webhook_ignored_when_no_event():
    subs = _FakeSubs(_sub(SubscriptionStatus.ACTIVE, external_ref="ext-1"))
    await _handler(subs, None).execute(rail=BillingRail.STRIPE, payload=b"{}", headers={})
    assert subs.saved is None
