"""Persistencia del billing (Flujo A). ``plans`` es catálogo global; las
``subscriptions`` son tenant-scoped (RLS + filtro explícito)."""

from __future__ import annotations

from sqlalchemy import delete, select

from app.domain.billing.entities import Plan, Subscription
from app.domain.billing.repository import PlanRepository, SubscriptionRepository
from app.domain.billing.value_objects import BillingRegion
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    plan_to_domain,
    plan_to_orm,
    subscription_to_domain,
    subscription_to_orm,
)
from app.infrastructure.persistence.models import PlanORM, SubscriptionORM


class SqlAlchemyPlanRepository(PlanRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def list_active(self, region: BillingRegion) -> list[Plan]:
        async with self._session_factory() as session:
            stmt = (
                select(PlanORM)
                .where(PlanORM.region == region.value, PlanORM.active.is_(True))
                .order_by(PlanORM.price_amount)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [plan_to_domain(row) for row in rows]

    async def list_all(self) -> list[Plan]:
        async with self._session_factory() as session:
            rows = (
                await session.execute(
                    select(PlanORM).order_by(PlanORM.region, PlanORM.tier, PlanORM.price_amount)
                )
            ).scalars().all()
            return [plan_to_domain(row) for row in rows]

    async def get_by_id(self, plan_id: str) -> Plan | None:
        async with self._session_factory() as session:
            row = (
                await session.execute(select(PlanORM).where(PlanORM.id == plan_id))
            ).scalar_one_or_none()
            return plan_to_domain(row) if row is not None else None

    async def upsert(self, plan: Plan) -> None:
        async with self._session_factory() as session:
            await session.merge(plan_to_orm(plan))

    async def delete(self, plan_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(delete(PlanORM).where(PlanORM.id == plan_id))


class SqlAlchemySubscriptionRepository(SubscriptionRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_tenant(self, tenant_id: str) -> Subscription | None:
        async with self._session_factory() as session:
            row = (
                await session.execute(
                    select(SubscriptionORM).where(SubscriptionORM.tenant_id == tenant_id)
                )
            ).scalar_one_or_none()
            return subscription_to_domain(row) if row is not None else None

    async def get_by_external_ref(self, external_ref: str) -> Subscription | None:
        async with self._session_factory() as session:
            row = (
                await session.execute(
                    select(SubscriptionORM).where(
                        SubscriptionORM.external_ref == external_ref
                    )
                )
            ).scalar_one_or_none()
            return subscription_to_domain(row) if row is not None else None

    async def add(self, subscription: Subscription) -> None:
        async with self._session_factory() as session:
            session.add(subscription_to_orm(subscription))

    async def save(self, subscription: Subscription) -> None:
        async with self._session_factory() as session:
            await session.merge(subscription_to_orm(subscription))
