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
    # OJO: ``sales`` es lo **COBRADO**, no lo vendido — Σ de cobros INFLOW
    # confirmados. El nombre engaña y se conserva a propósito: lo lee una app
    # móvil ya publicada, y renombrar el campo le mostraría $0. En la UI se
    # rotula "Cobrado"; lo vendido (devengado) vive en `analytics.RevenueSummary`
    # como ``sales_amount``. Dos libros distintos, dos lugares distintos.
    sales: int  # confirmed INFLOW total (minor units) — es COBRADO
    expenses: int  # confirmed OUTFLOW total (minor units)
    net: int  # sales − expenses (bruto de comisiones)
    active_orders: int  # not PAID/CANCELLED
    paid_orders: int
    avg_ticket: int  # sales / paid_orders (0 if none)
    payment_count: int  # confirmed inflow payments
    # Comisiones (slice B): neto financiero cobrado (tras comisión de pasarela) y
    # total de comisiones. Sin tasas → collected_net == sales, fees_total == 0 (paridad).
    collected_net: int = 0
    fees_total: int = 0
    # La ganancia que efectivamente muestran las pantallas: lo que quedó en la
    # cuenta tras la comisión, menos los egresos. Se calcula acá y no en cada
    # cliente porque estaba escrita dos veces —una en el .tsx de Reportes y otra
    # en el .dart del móvil— y esa es la vía por la que una quinta definición de
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
