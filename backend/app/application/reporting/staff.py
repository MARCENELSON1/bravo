"""Staff report read model (CQRS-lite): hours + overtime (from the timeclock)
crossed with tables/sales attributed by ``Order.waiter_id``. Behind a port so
the use case stays free of SQLAlchemy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from app.domain.identity.ports import TenantContext


@dataclass(frozen=True)
class StaffReportRow:
    user_id: str
    email: str
    worked_minutes: int
    overtime_minutes: int  # Σ daily_overtime over the period, vs the tenant standard
    tables_served: int  # distinct tables of the worker's PAID orders
    sales_amount: int  # total of the worker's PAID orders (minor units)
    hourly_rate_amount: int | None  # valor/hora (minor units); None → sin cargar
    currency: str


@dataclass(frozen=True)
class StaffReport:
    currency: str
    rows: list[StaffReportRow]


class StaffReportReadModel(ABC):
    @abstractmethod
    async def report(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> StaffReport: ...


class GetStaffReport:
    def __init__(
        self, read_model: StaffReportReadModel, tenant_context: TenantContext
    ) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> StaffReport:
        self._tenant_context.set(tenant_id)
        return await self._read_model.report(tenant_id, since=since, until=until)
