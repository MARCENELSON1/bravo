"""DTOs de la Pantalla Finanzas unificada. Un solo payload con los KPIs vitales
(cada uno con su comparativo vs período previo y rango sano), los diagnósticos en
lenguaje natural y el margen de contribución por producto."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FinanceKpi:
    """Un KPI con su comparativo. ``kind`` distingue ratio (valor en bps sobre
    ventas) de money (unidad mínima). ``status`` colorea el rango sano:
    healthy/warn/alert/neutral. ``healthy_low``/``healthy_high`` en bps (None si
    no aplica, p. ej. KPIs de plata)."""

    key: str
    kind: str  # "ratio" (bps) | "money" (minor units)
    value: int
    previous: int
    delta: int  # value - previous
    healthy_low: int | None
    healthy_high: int | None
    status: str  # healthy | warn | alert | neutral


@dataclass(frozen=True)
class FinanceDiagnostic:
    """Un diagnóstico narrado (reusa los insights del Asesor)."""

    code: str
    severity: str
    bucket: str
    title: str
    body: str
    action: str


@dataclass(frozen=True)
class ProductMargin:
    """Margen de contribución de un producto en pesos (no en %): lo que deja."""

    product_id: str
    product_name: str
    units_sold: int
    sales_amount: int
    margin_amount: int  # sales − food_cost


@dataclass(frozen=True)
class FinanceOverview:
    currency: str
    period_days: int
    configured: bool  # False si el tenant no cargó costos fijos (labor/otros = 0)
    kpis: list[FinanceKpi]
    diagnostics: list[FinanceDiagnostic]
    product_margins: list[ProductMargin]
    summary: str | None
