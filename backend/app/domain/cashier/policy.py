from __future__ import annotations

from abc import ABC, abstractmethod


class CashSessionPolicy(ABC):
    """Política operativa por tenant: ¿exige una caja abierta para poder cobrar?
    (guarda B3). Port de UNA sola pregunta para que el path de cobro no dependa del
    agregado Tenant ni del perfil de costos. El adapter lee la columna directo →
    sin round-trip por la entidad Tenant (evita lost-update)."""

    @abstractmethod
    async def requires_open_cash_session(self, tenant_id: str) -> bool: ...
