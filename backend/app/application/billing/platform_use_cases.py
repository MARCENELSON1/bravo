"""Gestión del catálogo global de planes desde el panel de plataforma
(super-admin). Los planes son data de configuración, no tenant-scoped."""

from __future__ import annotations

from uuid import uuid4

from app.domain.billing.entities import Plan
from app.domain.billing.exceptions import InvalidPlanFeature, PlanNotFound
from app.domain.billing.features import is_known_feature
from app.domain.billing.repository import PlanRepository
from app.domain.billing.value_objects import BillingInterval, BillingRegion, PlanTier
from app.domain.shared.money import Money


class ListAllPlans:
    def __init__(self, plans: PlanRepository) -> None:
        self._plans = plans

    async def execute(self) -> list[Plan]:
        return await self._plans.list_all()


class SavePlan:
    """Crea (sin id) o actualiza (con id) un plan del catálogo. Valida que las
    features pertenezcan al catálogo. Devuelve el plan guardado."""

    def __init__(self, plans: PlanRepository) -> None:
        self._plans = plans

    async def execute(
        self,
        *,
        id: str | None,
        tier: PlanTier,
        region: BillingRegion,
        amount: int,
        currency: str,
        interval: BillingInterval,
        features: list[str],
        active: bool,
    ) -> Plan:
        for feature in features:
            if not is_known_feature(feature):
                raise InvalidPlanFeature()
        plan = Plan(
            id=id or str(uuid4()),
            tier=tier,
            region=region,
            price=Money(amount, currency),
            interval=interval,
            features=frozenset(features),
            active=active,
        )
        await self._plans.upsert(plan)
        return plan


class DeletePlan:
    def __init__(self, plans: PlanRepository) -> None:
        self._plans = plans

    async def execute(self, *, plan_id: str) -> None:
        if await self._plans.get_by_id(plan_id) is None:
            raise PlanNotFound()
        await self._plans.delete(plan_id)
