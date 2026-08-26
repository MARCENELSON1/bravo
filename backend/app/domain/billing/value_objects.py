from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PlanTier(StrEnum):
    """Nivel del plan de suscripción. Extensible (agregar tiers no rompe nada)."""

    BASIC = "BASIC"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


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


@dataclass(frozen=True)
class CheckoutSession:
    """Resultado de iniciar un checkout en la pasarela: la URL a la que se
    redirige al usuario para pagar, y el id de referencia en la pasarela."""

    url: str
    external_ref: str


class BillingEventType(StrEnum):
    """Evento de billing normalizado (agnóstico de la pasarela). El adapter
    traduce los eventos crudos de Stripe/MercadoPago a estos tres."""

    ACTIVATED = "ACTIVATED"  # pago inicial OK / suscripción activa
    PAYMENT_FAILED = "PAYMENT_FAILED"  # cobro fallido → gracia
    CANCELED = "CANCELED"  # cancelada en la pasarela


@dataclass(frozen=True)
class BillingEvent:
    """Un evento de webhook ya verificado y normalizado. ``tenant_id`` viene de la
    metadata que pusimos al crear el checkout (así el webhook, que no lleva auth,
    resuelve el tenant sin depender de la IP)."""

    tenant_id: str
    external_ref: str
    type: BillingEventType
