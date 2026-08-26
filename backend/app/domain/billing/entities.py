from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.billing.exceptions import InvalidSubscriptionTransition
from app.domain.billing.value_objects import (
    BillingInterval,
    BillingRail,
    BillingRegion,
    PlanTier,
    SubscriptionStatus,
)
from app.domain.shared.money import Money


@dataclass(frozen=True)
class Plan:
    """Un plan del catálogo: un tier en una región, con su precio en la moneda de
    esa región. El mismo tier existe una vez por región (BASIC/AR en ARS,
    BASIC/INTL en USD). ``features`` son las capacidades que el tier habilita
    (claves libres; el gating chequea pertenencia). Es data de catálogo, inmutable."""

    id: str
    tier: PlanTier
    region: BillingRegion
    price: Money
    interval: BillingInterval = BillingInterval.MONTH
    features: frozenset[str] = field(default_factory=frozenset)
    active: bool = True


# Transiciones válidas del estado de la suscripción (destino ← orígenes).
_ALLOWED_SOURCES: dict[SubscriptionStatus, frozenset[SubscriptionStatus]] = {
    SubscriptionStatus.TRIALING: frozenset({SubscriptionStatus.INCOMPLETE}),
    SubscriptionStatus.ACTIVE: frozenset(
        {
            SubscriptionStatus.INCOMPLETE,
            SubscriptionStatus.TRIALING,
            SubscriptionStatus.PAST_DUE,
        }
    ),
    SubscriptionStatus.PAST_DUE: frozenset({SubscriptionStatus.ACTIVE}),
    # CANCELED se puede alcanzar desde cualquier estado no-terminal (ver cancel()).
}

_ACCESS_GRANTING = frozenset(
    {SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE}
)


@dataclass
class Subscription:
    """La suscripción de un tenant a un plan. Nace INCOMPLETE (esperando el primer
    pago) y avanza por su máquina de estados. ``rail`` es la pasarela real que la
    cobra (debe ser la de la región del plan — lo valida la policy al crearla).
    ``external_ref`` es el id en la pasarela (sub_… de Stripe / preapproval de MP)."""

    id: str
    tenant_id: str
    plan_id: str
    region: BillingRegion
    rail: BillingRail
    status: SubscriptionStatus = SubscriptionStatus.INCOMPLETE
    external_ref: str | None = None
    trial_end: datetime | None = None
    current_period_end: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def grants_access(self) -> bool:
        """Si la suscripción habilita el uso del sistema. PAST_DUE mantiene acceso
        (período de gracia / dunning) hasta que se cancela."""
        return self.status in _ACCESS_GRANTING

    def start_trial(self, trial_end: datetime) -> None:
        self._transition(SubscriptionStatus.TRIALING)
        self.trial_end = trial_end

    def activate(self, current_period_end: datetime | None = None) -> None:
        self._transition(SubscriptionStatus.ACTIVE)
        if current_period_end is not None:
            self.current_period_end = current_period_end

    def mark_past_due(self) -> None:
        self._transition(SubscriptionStatus.PAST_DUE)

    def cancel(self) -> None:
        if self.status is SubscriptionStatus.CANCELED:
            raise InvalidSubscriptionTransition()
        self.status = SubscriptionStatus.CANCELED

    def _transition(self, target: SubscriptionStatus) -> None:
        if self.status not in _ALLOWED_SOURCES.get(target, frozenset()):
            raise InvalidSubscriptionTransition()
        self.status = target
