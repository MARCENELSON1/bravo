"""Rebuild manual de los snapshots diarios de Finanzas (Tanda F). Reconstruye
todo desde sale_facts; necesario para backfill del historial previo o si se
sospecha deriva. La invalidación normal es incremental (en el projector)."""

from __future__ import annotations

from app.application.analytics.ports import FinanceSnapshotRebuilder
from app.domain.identity.ports import TenantContext


class RebuildFinanceSnapshots:
    def __init__(
        self, rebuilder: FinanceSnapshotRebuilder, tenant_context: TenantContext
    ) -> None:
        self._rebuilder = rebuilder
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> int:
        self._tenant_context.set(tenant_id)
        return await self._rebuilder.rebuild(tenant_id)
