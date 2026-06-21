"""Gold use cases: set the tenant context and delegate to the read models."""

from __future__ import annotations

from datetime import datetime

from app.application.analytics.read_models import (
    PaymentMixReadModel,
    PaymentMixRow,
    ProductPerformanceReadModel,
    ProductPerformanceRow,
    RevenueReadModel,
    RevenueSummary,
)
from app.domain.identity.ports import TenantContext


class GetRevenueSummary:
    def __init__(
        self, read_model: RevenueReadModel, tenant_context: TenantContext
    ) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> RevenueSummary:
        self._tenant_context.set(tenant_id)
        return await self._read_model.summary(tenant_id, since=since, until=until)


class GetPaymentMix:
    def __init__(
        self, read_model: PaymentMixReadModel, tenant_context: TenantContext
    ) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[PaymentMixRow]:
        self._tenant_context.set(tenant_id)
        return await self._read_model.mix(tenant_id, since=since, until=until)


class GetProductPerformance:
    def __init__(
        self, read_model: ProductPerformanceReadModel, tenant_context: TenantContext
    ) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 10,
    ) -> list[ProductPerformanceRow]:
        self._tenant_context.set(tenant_id)
        return await self._read_model.top(tenant_id, since=since, until=until, limit=limit)
