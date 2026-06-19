from __future__ import annotations

from app.context import get_current_tenant, set_current_tenant
from app.domain.identity.ports import TenantContext


class ContextVarTenantContext(TenantContext):
    """Tenant context backed by the request-scoped ContextVar in ``app.context``."""

    def set(self, tenant_id: str) -> None:
        set_current_tenant(tenant_id)

    def get(self) -> str | None:
        return get_current_tenant()
