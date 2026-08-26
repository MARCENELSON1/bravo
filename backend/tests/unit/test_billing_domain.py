from __future__ import annotations

from datetime import datetime

import pytest

from app.domain.billing.entities import Plan, Subscription
from app.domain.billing.exceptions import (
    InvalidSubscriptionTransition,
    RailNotAllowedForRegion,
)
from app.domain.billing.policy import assert_rail_allowed, feature_allowed
from app.domain.billing.value_objects import (
    BillingInterval,
    BillingRail,
    BillingRegion,
    PlanTier,
    SubscriptionStatus,
    rail_for_region,
)
from app.domain.shared.money import Money

_TS = datetime(2026, 1, 1)


def _plan(features: frozenset[str] = frozenset()) -> Plan:
    return Plan(
        id="p1",
        tier=PlanTier.PRO,
        region=BillingRegion.INTL,
        price=Money(4900, "USD"),
        interval=BillingInterval.MONTH,
        features=features,
    )


def _sub(status: SubscriptionStatus = SubscriptionStatus.INCOMPLETE) -> Subscription:
    return Subscription(
        id="s1",
        tenant_id="t1",
        plan_id="p1",
        region=BillingRegion.INTL,
        rail=BillingRail.STRIPE,
        status=status,
    )


# --- riel por región (anti-arbitraje) ---------------------------------------


def test_rail_for_region():
    assert rail_for_region(BillingRegion.AR) is BillingRail.MERCADOPAGO
    assert rail_for_region(BillingRegion.INTL) is BillingRail.STRIPE


def test_assert_rail_allowed_ok():
    assert_rail_allowed(BillingRegion.AR, BillingRail.MERCADOPAGO)
    assert_rail_allowed(BillingRegion.INTL, BillingRail.STRIPE)


def test_assert_rail_rejects_cross_region():
    # El plan AR NO se puede cobrar por Stripe (saltearía el pricing regional).
    with pytest.raises(RailNotAllowedForRegion):
        assert_rail_allowed(BillingRegion.AR, BillingRail.STRIPE)
    with pytest.raises(RailNotAllowedForRegion):
        assert_rail_allowed(BillingRegion.INTL, BillingRail.MERCADOPAGO)


# --- máquina de estados de la suscripción -----------------------------------


def test_new_subscription_is_incomplete_without_access():
    sub = _sub()
    assert sub.status is SubscriptionStatus.INCOMPLETE
    assert sub.grants_access() is False


def test_trial_then_activate():
    sub = _sub()
    sub.start_trial(_TS)
    assert sub.status is SubscriptionStatus.TRIALING
    assert sub.trial_end == _TS
    assert sub.grants_access() is True
    sub.activate(current_period_end=_TS)
    assert sub.status is SubscriptionStatus.ACTIVE
    assert sub.current_period_end == _TS
    assert sub.grants_access() is True


def test_activate_directly_from_incomplete():
    sub = _sub()
    sub.activate()
    assert sub.status is SubscriptionStatus.ACTIVE


def test_past_due_keeps_access_and_recovers():
    sub = _sub(SubscriptionStatus.ACTIVE)
    sub.mark_past_due()
    assert sub.status is SubscriptionStatus.PAST_DUE
    assert sub.grants_access() is True  # gracia
    sub.activate()
    assert sub.status is SubscriptionStatus.ACTIVE


def test_cancel_from_active_and_is_terminal():
    sub = _sub(SubscriptionStatus.ACTIVE)
    sub.cancel()
    assert sub.status is SubscriptionStatus.CANCELED
    assert sub.grants_access() is False
    with pytest.raises(InvalidSubscriptionTransition):
        sub.cancel()  # ya cancelada


def test_invalid_transitions_raise():
    # No se puede pasar a TRIALING una suscripción ya activa.
    with pytest.raises(InvalidSubscriptionTransition):
        _sub(SubscriptionStatus.ACTIVE).start_trial(_TS)
    # No se puede reactivar una cancelada.
    with pytest.raises(InvalidSubscriptionTransition):
        _sub(SubscriptionStatus.CANCELED).activate()
    # PAST_DUE solo desde ACTIVE.
    with pytest.raises(InvalidSubscriptionTransition):
        _sub(SubscriptionStatus.INCOMPLETE).mark_past_due()


# --- gating por plan ---------------------------------------------------------


def test_feature_allowed_when_active_and_plan_has_it():
    sub = _sub(SubscriptionStatus.ACTIVE)
    plan = _plan(frozenset({"copilot"}))
    assert feature_allowed(sub, plan, "copilot") is True
    assert feature_allowed(sub, plan, "multi_location") is False  # no está en el plan


def test_feature_denied_without_subscription_or_plan():
    assert feature_allowed(None, _plan(frozenset({"copilot"})), "copilot") is False
    assert feature_allowed(_sub(SubscriptionStatus.ACTIVE), None, "copilot") is False


def test_feature_denied_when_subscription_not_active():
    plan = _plan(frozenset({"copilot"}))
    assert feature_allowed(_sub(SubscriptionStatus.INCOMPLETE), plan, "copilot") is False
    assert feature_allowed(_sub(SubscriptionStatus.CANCELED), plan, "copilot") is False
