from __future__ import annotations

from pydantic import BaseModel


class PlanResponse(BaseModel):
    id: str
    tier: str
    region: str
    amount: int  # minor units (centavos)
    currency: str
    interval: str
    features: list[str]


class CheckoutRequest(BaseModel):
    plan_id: str


class CheckoutResponse(BaseModel):
    url: str  # a dónde redirigir al usuario para pagar (checkout hosteado)


class SubscriptionResponse(BaseModel):
    status: str
    plan_id: str
    region: str
    rail: str
    grants_access: bool  # si la suscripción habilita el uso (trial/active/gracia)
    current_period_end: str | None = None
