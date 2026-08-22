from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.identity.ports import TenantContext


class ReportExportKind(StrEnum):
    """The three accountant exports (Fase 10)."""

    SALES = "sales"  # ventas por día
    EXPENSES = "expenses"  # gastos itemizados
    VAT_SALES = "vat_sales"  # libro IVA ventas (desde comprobantes AFIP)


@dataclass(frozen=True)
class ExportTable:
    """A tabular export ready to serialize (headers + string rows). Amounts come
    pre-formatted as AR decimals (coma), so the CSV layer only quotes/joins."""

    headers: list[str]
    rows: list[list[str]]


class ReportExportReadModel(ABC):
    """Builds the accountant export tables for a window. Scoped by ``tenant_id``
    (RLS + explicit filter); read-only."""

    @abstractmethod
    async def sales_by_day(
        self, tenant_id: str, *, since: datetime | None, until: datetime | None
    ) -> ExportTable: ...

    @abstractmethod
    async def expenses(
        self, tenant_id: str, *, since: datetime | None, until: datetime | None
    ) -> ExportTable: ...

    @abstractmethod
    async def vat_sales(
        self, tenant_id: str, *, since: datetime | None, until: datetime | None
    ) -> ExportTable: ...


class ExportReport:
    """One entry point for the three CSV exports (dispatches by ``kind``)."""

    def __init__(
        self, read_model: ReportExportReadModel, tenant_context: TenantContext
    ) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        kind: ReportExportKind,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> ExportTable:
        self._tenant_context.set(tenant_id)
        if kind is ReportExportKind.SALES:
            return await self._read_model.sales_by_day(tenant_id, since=since, until=until)
        if kind is ReportExportKind.EXPENSES:
            return await self._read_model.expenses(tenant_id, since=since, until=until)
        return await self._read_model.vat_sales(tenant_id, since=since, until=until)
