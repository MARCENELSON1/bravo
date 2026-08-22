"""Pantalla Finanzas unificada: compone el motor del Asesor (KPIs + comparativo
con período previo + diagnósticos narrados) con el rendimiento por producto, y
arma un solo payload con los KPIs vitales etiquetados con su rango sano.

Reusa `GetAdvisorReport` (no reescribe la inteligencia). Cuando llegue la capa de
snapshots (tanda F), el swap es a nivel del read model del Asesor."""

from __future__ import annotations

import calendar
from abc import ABC, abstractmethod
from datetime import datetime

from app.application.advisor.report import GetAdvisorReport
from app.application.analytics.use_cases import GetProductPerformance
from app.application.clock import utcnow
from app.application.finance.dtos import (
    ExpenseBreakdown,
    FinanceDiagnostic,
    FinanceKpi,
    FinanceOverview,
    FinanceProjection,
    MovementRow,
    ProductDetail,
    ProductMargin,
)
from app.domain.advisor.entities import AdvisorSettings
from app.domain.advisor.kpis import AdvisorKpis
from app.domain.advisor.repository import AdvisorSettingsRepository
from app.domain.identity.ports import TenantContext

# Rangos sanos en bps sobre ventas (del doc "KPIs gastronómicos vitales").
_FOOD_COST_HEALTHY = (2800, 3500)  # 28%–35%
_LABOR_COST_HEALTHY = (2500, 3500)  # 25%–35%
_PRIME_COST_HEALTHY_HIGH = 6000  # <60% viable
_PRIME_COST_ALERT = 6500  # >65% el dueño trabaja para proveedores/empleados
_WASTE_HEALTHY_HIGH = 300  # <3% de la facturación


def _ratio_bps(part: int, whole: int) -> int:
    return round(part * 10000 / whole) if whole else 0


def _cost_status(value: int, high: int, alert: int) -> str:
    """Para costos: por debajo del techo es sano; arriba, warn y luego alert."""
    if value > alert:
        return "alert"
    if value > high:
        return "warn"
    return "healthy"


def _ratio_kpi(
    key: str,
    cur: AdvisorKpis,
    prev: AdvisorKpis | None,
    value: int,
    prev_value: int,
    *,
    healthy_low: int | None,
    healthy_high: int,
    alert: int,
) -> FinanceKpi:
    previous = prev_value if prev is not None else 0
    return FinanceKpi(
        key=key,
        kind="ratio",
        value=value,
        previous=previous,
        delta=value - previous,
        healthy_low=healthy_low,
        healthy_high=healthy_high,
        status=_cost_status(value, healthy_high, alert),
    )


def _money_kpi(
    key: str, value: int, prev_value: int, prev: AdvisorKpis | None, status: str
) -> FinanceKpi:
    previous = prev_value if prev is not None else 0
    return FinanceKpi(
        key=key,
        kind="money",
        value=value,
        previous=previous,
        delta=value - previous,
        healthy_low=None,
        healthy_high=None,
        status=status,
    )


def _project_month_end(
    kpis: AdvisorKpis, since: datetime | None, until: datetime | None
) -> FinanceProjection | None:
    """Proyección lineal del cierre del mes en curso. Solo cuando la ventana es el
    mes actual a la fecha (since = día 1 del mes corriente); None en otro caso."""
    now = until or utcnow()
    if since is None or since.year != now.year or since.month != now.month or since.day != 1:
        return None
    month_days = calendar.monthrange(now.year, now.month)[1]
    elapsed = (now.date() - since.date()).days + 1
    if elapsed < 1 or elapsed >= month_days:
        return None  # mes cerrado / último día → la proyección sería el acumulado
    factor = month_days / elapsed
    return FinanceProjection(
        sales_amount=round(kpis.sales_amount * factor),
        net_margin_amount=round(kpis.net_margin_amount * factor),
        month_days=month_days,
        elapsed_days=elapsed,
    )


class InventoryValueReadModel(ABC):
    """Valor del inventario a mano (Σ stock × costo unitario), en unidad mínima.
    Scopeado por ``tenant_id`` (RLS + filtro explícito)."""

    @abstractmethod
    async def total_value(self, tenant_id: str) -> int: ...


def _revpash_kpi(
    cur: AdvisorKpis, prev: AdvisorKpis | None, settings: AdvisorSettings | None
) -> FinanceKpi:
    """RevPASH = ventas / (asientos × horas abiertas × días). $ por asiento-hora."""
    seats = settings.seats if settings else 0
    open_min = settings.daily_open_minutes if settings else 0

    def revpash(sales: int, days: int) -> int:
        seat_hours = seats * (open_min / 60) * max(days, 1)
        return round(sales / seat_hours) if seat_hours > 0 else 0

    value = revpash(cur.sales_amount, cur.period_days)
    previous = revpash(prev.sales_amount, prev.period_days) if prev else 0
    return FinanceKpi(
        key="revpash", kind="money", value=value, previous=previous,
        delta=value - previous, healthy_low=None, healthy_high=None, status="neutral",
    )


def _turnover_kpi(cur: AdvisorKpis, inventory_value: int) -> FinanceKpi:
    """Rotación de inventario = COGS del período / valor de inventario. En
    centésimas de 'veces' (250 = 2,5×). Sin histórico de inventario aún → sin
    comparativo (delta 0)."""
    value = round(cur.food_cost_amount * 100 / inventory_value) if inventory_value > 0 else 0
    return FinanceKpi(
        key="inventory_turnover", kind="turnover", value=value, previous=value,
        delta=0, healthy_low=None, healthy_high=None, status="neutral",
    )


class FinanceProductDetailReadModel(ABC):
    """Líneas de venta de un producto en una ventana (drill-down). Scopeado por
    ``tenant_id`` (RLS + filtro explícito)."""

    @abstractmethod
    async def detail(
        self,
        tenant_id: str,
        product_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> ProductDetail: ...


def _build_finance_kpis(cur: AdvisorKpis, prev: AdvisorKpis | None) -> list[FinanceKpi]:
    waste_bps = _ratio_bps(cur.waste_amount, cur.sales_amount)
    prev_waste_bps = _ratio_bps(prev.waste_amount, prev.sales_amount) if prev else 0
    return [
        _ratio_kpi(
            "prime_cost", cur, prev, cur.prime_cost_ratio_bps,
            prev.prime_cost_ratio_bps if prev else 0,
            healthy_low=None, healthy_high=_PRIME_COST_HEALTHY_HIGH, alert=_PRIME_COST_ALERT,
        ),
        _ratio_kpi(
            "food_cost", cur, prev, cur.food_cost_ratio_bps,
            prev.food_cost_ratio_bps if prev else 0,
            healthy_low=_FOOD_COST_HEALTHY[0], healthy_high=_FOOD_COST_HEALTHY[1],
            alert=round(_FOOD_COST_HEALTHY[1] * 1.1),
        ),
        _ratio_kpi(
            "labor_cost", cur, prev, cur.labor_cost_ratio_bps,
            prev.labor_cost_ratio_bps if prev else 0,
            healthy_low=_LABOR_COST_HEALTHY[0], healthy_high=_LABOR_COST_HEALTHY[1],
            alert=round(_LABOR_COST_HEALTHY[1] * 1.1),
        ),
        _ratio_kpi(
            "waste", cur, prev, waste_bps, prev_waste_bps,
            healthy_low=None, healthy_high=_WASTE_HEALTHY_HIGH,
            alert=round(_WASTE_HEALTHY_HIGH * 1.1),
        ),
        _money_kpi(
            "net_margin", cur.net_margin_amount,
            prev.net_margin_amount if prev else 0, prev,
            status="healthy" if cur.net_margin_amount > 0 else "alert",
        ),
        _money_kpi(
            "gross_margin", cur.gross_margin_amount,
            prev.gross_margin_amount if prev else 0, prev, status="neutral",
        ),
        _money_kpi(
            "break_even", cur.break_even_amount,
            prev.break_even_amount if prev else 0, prev, status="neutral",
        ),
    ]


class FinanceCommissionsReadModel(ABC):
    """Comisiones de pasarela cobradas en la ventana + lo cobrado neto de ellas
    (sobre cobros CONFIRMED/INFLOW). Scopeado por ``tenant_id`` (RLS + filtro).
    Sin tasas cargadas → (0, bruto). Eje de cobranza, ortogonal al margen de IVA."""

    @abstractmethod
    async def fees_and_net(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> tuple[int, int]:
        """Devuelve (comisiones_total, cobrado_neto) en unidad mínima."""
        ...


class GetFinanceOverview:
    """Un solo payload para la Pantalla Finanzas: KPIs vitales con comparativo,
    diagnósticos y margen por producto."""

    def __init__(
        self,
        advisor: GetAdvisorReport,
        products: GetProductPerformance,
        settings: AdvisorSettingsRepository,
        inventory: InventoryValueReadModel,
        commissions: FinanceCommissionsReadModel,
        tenant_context: TenantContext,
    ) -> None:
        self._advisor = advisor
        self._products = products
        self._settings = settings
        self._inventory = inventory
        self._commissions = commissions
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> FinanceOverview:
        self._tenant_context.set(tenant_id)
        report = await self._advisor.execute(tenant_id=tenant_id, since=since, until=until)
        rows = await self._products.execute(
            tenant_id=tenant_id, since=since, until=until, limit=10
        )
        settings = await self._settings.get(tenant_id)
        inventory_value = await self._inventory.total_value(tenant_id)
        commissions, collected_net = await self._commissions.fees_and_net(
            tenant_id, since=since, until=until
        )
        kpis = _build_finance_kpis(report.kpis, report.previous)
        kpis.append(_revpash_kpi(report.kpis, report.previous, settings))
        kpis.append(_turnover_kpi(report.kpis, inventory_value))
        return FinanceOverview(
            currency=report.kpis.currency,
            period_days=report.kpis.period_days,
            configured=report.kpis.configured,
            kpis=kpis,
            diagnostics=[
                FinanceDiagnostic(
                    code=i.code,
                    severity=i.severity,
                    bucket=i.bucket,
                    title=i.title,
                    body=i.body,
                    action=i.action,
                )
                for i in report.insights
            ],
            product_margins=[
                ProductMargin(
                    product_id=r.product_id,
                    product_name=r.product_name,
                    units_sold=r.units_sold,
                    sales_amount=r.sales_amount,
                    margin_amount=r.margin_amount,
                )
                for r in rows
            ],
            summary=report.summary,
            projection=_project_month_end(report.kpis, since, until),
            commissions_amount=commissions,
            collected_net_amount=collected_net,
        )


class GetProductDetail:
    """Drill-down: las líneas de venta de un producto en la ventana (≤3 clics
    desde la Pantalla Finanzas)."""

    def __init__(
        self, read_model: FinanceProductDetailReadModel, tenant_context: TenantContext
    ) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        product_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> ProductDetail:
        self._tenant_context.set(tenant_id)
        return await self._read_model.detail(tenant_id, product_id, since=since, until=until)


class ExpenseBreakdownReadModel(ABC):
    """Egresos agrupados por categoría en la ventana + comparativo con el período
    previo. Scopeado por ``tenant_id`` (RLS + filtro explícito)."""

    @abstractmethod
    async def breakdown(
        self, tenant_id: str, *, since: datetime | None = None, until: datetime | None = None
    ) -> ExpenseBreakdown: ...


class RecentMovementsReadModel(ABC):
    """Últimos movimientos (cobros + egresos) en la ventana. Scopeado por tenant."""

    @abstractmethod
    async def recent(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 20,
    ) -> list[MovementRow]: ...


class GetExpenseBreakdown:
    def __init__(
        self, read_model: ExpenseBreakdownReadModel, tenant_context: TenantContext
    ) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, since: datetime | None = None, until: datetime | None = None
    ) -> ExpenseBreakdown:
        self._tenant_context.set(tenant_id)
        return await self._read_model.breakdown(tenant_id, since=since, until=until)


class GetRecentMovements:
    def __init__(
        self, read_model: RecentMovementsReadModel, tenant_context: TenantContext
    ) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 20,
    ) -> list[MovementRow]:
        self._tenant_context.set(tenant_id)
        return await self._read_model.recent(tenant_id, since=since, until=until, limit=limit)
