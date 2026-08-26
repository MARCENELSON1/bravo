"""Casos de uso del billing del SaaS (Flujo A). Provider-agnósticos: dependen de
los puertos (repos + gateway resolver), no de Stripe/MercadoPago."""

from __future__ import annotations

from uuid import uuid4

from app.domain.billing.entities import Subscription
from app.domain.billing.exceptions import (
    PlanNotFound,
    SubscriptionAlreadyActive,
    SubscriptionNotFound,
)
from app.domain.billing.policy import assert_rail_allowed
from app.domain.billing.ports import BillingGatewayResolver
from app.domain.billing.repository import PlanRepository, SubscriptionRepository
from app.domain.billing.value_objects import (
    BillingEvent,
    BillingEventType,
    BillingRail,
    SubscriptionStatus,
    rail_for_region,
)
from app.domain.identity.ports import TenantContext


class StartSubscriptionCheckout:
    """Inicia el checkout de una suscripción a un plan. Crea la suscripción local
    (INCOMPLETE) y devuelve la URL de pago de la pasarela de la región del plan.
    El candado anti-arbitraje se materializa acá: el riel (y por ende la pasarela)
    lo determina la región del plan, no lo elige el cliente."""

    def __init__(
        self,
        plans: PlanRepository,
        subscriptions: SubscriptionRepository,
        gateways: BillingGatewayResolver,
        tenant_context: TenantContext,
    ) -> None:
        self._plans = plans
        self._subscriptions = subscriptions
        self._gateways = gateways
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, plan_id: str, success_url: str, cancel_url: str
    ) -> str:
        self._tenant_context.set(tenant_id)
        plan = await self._plans.get_by_id(plan_id)
        if plan is None:
            raise PlanNotFound()
        existing = await self._subscriptions.get_by_tenant(tenant_id)
        if existing is not None and existing.grants_access():
            raise SubscriptionAlreadyActive()

        rail = rail_for_region(plan.region)
        assert_rail_allowed(plan.region, rail)  # belt-and-suspenders del anti-arbitraje
        # Reusa la fila si había una cancelada (unique por tenant).
        subscription = Subscription(
            id=existing.id if existing is not None else str(uuid4()),
            tenant_id=tenant_id,
            plan_id=plan.id,
            region=plan.region,
            rail=rail,
        )
        session = await self._gateways.for_rail(rail).start_checkout(
            subscription=subscription,
            plan=plan,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        subscription.external_ref = session.external_ref
        if existing is not None:
            await self._subscriptions.save(subscription)
        else:
            await self._subscriptions.add(subscription)
        return session.url


class CancelSubscription:
    def __init__(
        self,
        subscriptions: SubscriptionRepository,
        gateways: BillingGatewayResolver,
        tenant_context: TenantContext,
    ) -> None:
        self._subscriptions = subscriptions
        self._gateways = gateways
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> None:
        self._tenant_context.set(tenant_id)
        subscription = await self._subscriptions.get_by_tenant(tenant_id)
        if subscription is None:
            raise SubscriptionNotFound()
        if subscription.status is SubscriptionStatus.CANCELED:
            return  # idempotente
        if subscription.external_ref is not None:
            await self._gateways.for_rail(subscription.rail).cancel(
                external_ref=subscription.external_ref
            )
        subscription.cancel()
        await self._subscriptions.save(subscription)


class HandleBillingWebhook:
    """Aplica un webhook (ya verificado y normalizado por el gateway) a la máquina
    de estados de la suscripción. Idempotente: reintentos de la pasarela no rompen
    ni doble-aplican."""

    def __init__(
        self,
        subscriptions: SubscriptionRepository,
        gateways: BillingGatewayResolver,
        tenant_context: TenantContext,
    ) -> None:
        self._subscriptions = subscriptions
        self._gateways = gateways
        self._tenant_context = tenant_context

    async def execute(self, *, rail: BillingRail, payload: bytes, signature: str) -> None:
        event = await self._gateways.for_rail(rail).parse_webhook(
            payload=payload, signature=signature
        )
        if event is None:
            return  # evento que no nos interesa
        self._tenant_context.set(event.tenant_id)
        subscription = await self._subscriptions.get_by_tenant(event.tenant_id)
        if subscription is None:
            return
        if self._apply(subscription, event):
            await self._subscriptions.save(subscription)

    @staticmethod
    def _apply(subscription: Subscription, event: BillingEvent) -> bool:
        """Devuelve si hubo un cambio que persistir. Cada rama es idempotente."""
        changed = False
        if event.type is BillingEventType.ACTIVATED:
            # Al activar, la pasarela nos da el id DURABLE de la suscripción
            # (Stripe sub_…), que reemplaza el del checkout (cs_…) para cancelar
            # y correlacionar eventos futuros.
            if subscription.external_ref != event.external_ref:
                subscription.external_ref = event.external_ref
                changed = True
            if subscription.status in (
                SubscriptionStatus.INCOMPLETE,
                SubscriptionStatus.TRIALING,
                SubscriptionStatus.PAST_DUE,
            ):
                subscription.activate()
                changed = True
        elif event.type is BillingEventType.PAYMENT_FAILED:
            if subscription.status is SubscriptionStatus.ACTIVE:
                subscription.mark_past_due()
                changed = True
        elif event.type is BillingEventType.CANCELED:
            if subscription.status is not SubscriptionStatus.CANCELED:
                subscription.cancel()
                changed = True
        return changed
