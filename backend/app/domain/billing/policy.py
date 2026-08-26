"""Reglas de negocio puras del billing: gating por plan y el candado
anti-arbitraje (el riel tiene que ser el de la región del plan)."""

from __future__ import annotations

from app.domain.billing.entities import Plan, Subscription
from app.domain.billing.exceptions import RailNotAllowedForRegion
from app.domain.billing.value_objects import BillingRail, BillingRegion, rail_for_region


def assert_rail_allowed(region: BillingRegion, rail: BillingRail) -> None:
    """Candado anti-arbitraje: el plan de una región solo se cobra por su riel
    (AR → MercadoPago, INTL → Stripe). Cobrar el plan AR por Stripe (o viceversa)
    es un intento de saltear el pricing regional → se rechaza."""
    if rail_for_region(region) is not rail:
        raise RailNotAllowedForRegion()


def feature_allowed(
    subscription: Subscription | None, plan: Plan | None, feature: str
) -> bool:
    """Si el tenant puede usar una capacidad pagada: necesita una suscripción que
    habilite acceso (TRIALING/ACTIVE/gracia) y que su plan incluya la feature.
    Sin suscripción o sin plan → no habilitada."""
    if subscription is None or plan is None:
        return False
    return subscription.grants_access() and feature in plan.features
