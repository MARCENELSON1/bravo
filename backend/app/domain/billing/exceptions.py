from __future__ import annotations

from app.domain.errors import DomainError


class PlanNotFound(DomainError):
    code = "plan_not_found"
    message = "No encontramos el plan indicado."


class SubscriptionNotFound(DomainError):
    code = "subscription_not_found"
    message = "El local no tiene una suscripción."


class InvalidSubscriptionTransition(DomainError):
    code = "invalid_subscription_transition"
    message = "La suscripción no puede cambiar a ese estado."


class RailNotAllowedForRegion(DomainError):
    """Anti-arbitraje: intentar cobrar un plan por un riel que no es el de su
    región (ej. el plan argentino por Stripe)."""

    code = "rail_not_allowed_for_region"
    message = "Ese medio de pago no está habilitado para la región del plan."


class SubscriptionAlreadyActive(DomainError):
    code = "subscription_already_active"
    message = "El local ya tiene una suscripción activa."


class InvalidBillingWebhook(DomainError):
    code = "invalid_billing_webhook"
    message = "La notificación de billing no es válida."
