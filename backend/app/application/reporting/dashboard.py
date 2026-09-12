"""Dashboard summary read model (CQRS-lite): a thin read-side over payments +
orders, behind a port so the use case stays free of SQLAlchemy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from app.domain.identity.ports import TenantContext


@dataclass(frozen=True)
class DashboardSummary:
    currency: str
    # Lo COBRADO: Σ de cobros INFLOW confirmados. Se llamaba ``sales``, que hacía
    # que esta pantalla y Analytics mostraran dos cifras distintas bajo la misma
    # palabra — lo vendido (devengado) vive aparte, en
    # ``analytics.RevenueSummary.sales_amount``. Dos libros, dos nombres.
    sales_collected: int  # minor units
    expenses: int  # confirmed OUTFLOW total (minor units)
    # Las dos ganancias del período, nombradas por su base para que no se puedan
    # confundir: una antes de la comisión de la pasarela y otra después.
    profit_gross_of_fees: int  # sales_collected − expenses
    active_orders: int  # not PAID/CANCELLED
    paid_orders: int
    avg_ticket: int  # sales_collected / paid_orders (0 if none)
    payment_count: int  # confirmed inflow payments
    # Comisiones (slice B): neto financiero cobrado (tras comisión de pasarela) y
    # total de comisiones. Sin tasas → collected_net == sales_collected, fees == 0.
    collected_net: int = 0
    fees_total: int = 0
    # La que muestran las pantallas. Se calcula acá y no en cada cliente porque
    # estaba escrita TRES veces —el .tsx de Reportes, el .dart de Reportes y el
    # .dart del Inicio— y esa es la vía por la que una definición más de
    # "ganancia" entra sin pasar por ningún caso de uso.
    profit_net_of_fees: int = 0


class DashboardReadModel(ABC):
    @abstractmethod
    async def summary(
        self,
        tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> DashboardSummary: ...


class GetDashboardSummary:
    def __init__(self, read_model: DashboardReadModel, tenant_context: TenantContext) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> DashboardSummary:
        # Guarda C (Home): ventana de fecha sobre los cobros/egresos para que "hoy"
        # signifique hoy. Sin since/until → all-time (paridad con antes).
        self._tenant_context.set(tenant_id)
        return await self._read_model.summary(tenant_id, since, until)
