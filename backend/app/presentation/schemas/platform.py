from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.billing.value_objects import BillingInterval, BillingRegion, PlanTier


class PlatformAccessResponse(BaseModel):
    platform_admin: bool


class FeatureResponse(BaseModel):
    key: str
    label: str


class PlatformPlanRequest(BaseModel):
    id: str | None = None  # None → crear; presente → actualizar
    tier: PlanTier
    region: BillingRegion
    amount: int = Field(ge=0)  # minor units (centavos)
    currency: str = Field(min_length=3, max_length=3)
    interval: BillingInterval = BillingInterval.MONTH
    features: list[str] = []
    active: bool = True


class PlatformPlanResponse(BaseModel):
    id: str
    tier: str
    region: str
    amount: int
    currency: str
    interval: str
    features: list[str]
    active: bool
