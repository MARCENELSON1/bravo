from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping

from app.domain.billing.entities import Plan, Subscription
from app.domain.billing.value_objects import BillingEvent, BillingRail, CheckoutSession


class BillingGateway(ABC):
    """Pasarela de cobro de la suscripción del SaaS (Flujo A). Adapters: Stripe
    (USD) y MercadoPago Preapproval (ARS). Provider-agnóstica: los use cases no
    saben cuál corre."""

    @abstractmethod
    async def start_checkout(
        self,
        *,
        subscription: Subscription,
        plan: Plan,
        success_url: str,
        cancel_url: str,
        payer_email: str | None = None,
    ) -> CheckoutSession:
        """Inicia un checkout hosteado para la suscripción y devuelve la URL de
        pago + la referencia en la pasarela. La metadata lleva el ``tenant_id`` y
        el id de la suscripción (para resolver el tenant en el webhook).
        ``payer_email`` es opcional para Stripe (pre-llena el checkout) pero
        obligatorio para MercadoPago Preapproval."""

    @abstractmethod
    async def cancel(self, *, external_ref: str) -> None:
        """Cancela la suscripción en la pasarela (idempotente)."""

    @abstractmethod
    async def parse_webhook(
        self, *, payload: bytes, headers: Mapping[str, str]
    ) -> BillingEvent | None:
        """Verifica la firma (desde los headers) y normaliza el evento crudo.
        Devuelve ``None`` si el evento no nos interesa; lanza si la firma es
        inválida. Recibe todos los headers porque cada pasarela firma distinto
        (Stripe: ``Stripe-Signature``; MercadoPago: ``x-signature`` + ``x-request-id``)."""


class BillingGatewayResolver(ABC):
    """Elige la pasarela por riel — el punto donde se materializa el candado
    anti-arbitraje (AR → MercadoPago, INTL → Stripe)."""

    @abstractmethod
    def for_rail(self, rail: BillingRail) -> BillingGateway: ...
