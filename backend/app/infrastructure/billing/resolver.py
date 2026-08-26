"""Resolver de pasarela por riel — materializa el candado anti-arbitraje:
STRIPE → Stripe (USD), MERCADOPAGO → MercadoPago (ARS)."""

from __future__ import annotations

from app.domain.billing.ports import BillingGateway, BillingGatewayResolver
from app.domain.billing.value_objects import BillingRail


class RailBillingGatewayResolver(BillingGatewayResolver):
    def __init__(self, *, stripe: BillingGateway, mercadopago: BillingGateway) -> None:
        self._by_rail: dict[BillingRail, BillingGateway] = {
            BillingRail.STRIPE: stripe,
            BillingRail.MERCADOPAGO: mercadopago,
        }

    def for_rail(self, rail: BillingRail) -> BillingGateway:
        return self._by_rail[rail]
