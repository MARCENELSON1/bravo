"""Backfill: project the sale_facts for PAID orders captured before the
projection existed (or anytime they are missing). Idempotent."""

from __future__ import annotations

from app.application.analytics.ports import SalesProjector
from app.domain.identity.ports import TenantContext
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import OrderStatus


class RebuildSalesFacts:
    def __init__(
        self,
        orders: OrderRepository,
        projector: SalesProjector,
        tenant_context: TenantContext,
    ) -> None:
        self._orders = orders
        self._projector = projector
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> int:
        """Project every PAID order without facts; returns the count processed."""
        self._tenant_context.set(tenant_id)
        paid_orders = await self._orders.list_by_status(tenant_id, OrderStatus.PAID)
        for order in paid_orders:
            await self._projector.project_order(tenant_id, order.id)  # idempotent
        return len(paid_orders)
