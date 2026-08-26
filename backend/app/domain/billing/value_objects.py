from __future__ import annotations

from enum import StrEnum


class PlanTier(StrEnum):
    """Nivel del plan de suscripción. Extensible (agregar tiers no rompe nada)."""

    BASIC = "BASIC"
    PRO = "PRO"


class BillingRegion(StrEnum):
    """Región de facturación del SaaS. Binaria: Argentina (precio local PPP) vs
    Internacional (precio full). Determina moneda y riel de cobro."""

    AR = "AR"
    INTL = "INTL"


class BillingInterval(StrEnum):
    MONTH = "MONTH"
    YEAR = "YEAR"


class BillingRail(StrEnum):
    """Pasarela por la que se cobra la suscripción. El riel es el candado
    anti-arbitraje: el plan AR solo se paga por MercadoPago (credenciales
    argentinas), el internacional por Stripe (USD)."""

    MERCADOPAGO = "MERCADOPAGO"
    STRIPE = "STRIPE"


class SubscriptionStatus(StrEnum):
    """Estado de la suscripción. Alineado con Stripe/MercadoPago:
    INCOMPLETE (creada, esperando el primer pago) → TRIALING/ACTIVE; ACTIVE ↔
    PAST_DUE (pago fallido, período de gracia); CANCELED es terminal."""

    INCOMPLETE = "INCOMPLETE"
    TRIALING = "TRIALING"
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    CANCELED = "CANCELED"


# El riel se deriva de la región (una sola fuente de verdad para el anti-arbitraje).
_RAIL_BY_REGION = {
    BillingRegion.AR: BillingRail.MERCADOPAGO,
    BillingRegion.INTL: BillingRail.STRIPE,
}


def rail_for_region(region: BillingRegion) -> BillingRail:
    """El riel de cobro que corresponde a una región. Puro."""
    return _RAIL_BY_REGION[region]
