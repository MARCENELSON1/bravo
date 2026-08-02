from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class CreateProductResult:
    product_id: str


# --- Productos v2 Tanda B: precios vs inflación + histórico + rotación --------


@dataclass(frozen=True)
class PriceChange:
    """One entry of a product's price log (append-only)."""

    changed_at: str  # ISO-8601
    old_price_amount: int | None
    new_price_amount: int


@dataclass(frozen=True)
class ProductPricingBase:
    """Raw pricing inputs for a product (read side, before applying inflation)."""

    product_id: str
    product_name: str
    current_price_amount: int
    last_change_at: datetime  # max(changed_at) o created_at del producto


@dataclass(frozen=True)
class ProductPricingRow:
    """Un producto con su precio actual, cuánto hace que no cambia y a cuánto
    "debería estar" según la inflación mensual estimada del tenant."""

    product_id: str
    product_name: str
    current_price_amount: int
    suggested_price_amount: int
    gap_amount: int  # suggested - current (>= 0 cuando quedó atrás)
    gap_bps: int  # gap / current en basis points
    days_since_change: int
    lagging: bool


@dataclass(frozen=True)
class PricingInsights:
    currency: str
    monthly_inflation_bps: int
    configured: bool  # hay inflación cargada (> 0)
    rows: list[ProductPricingRow] = field(default_factory=list)


@dataclass(frozen=True)
class ProductPriceHistory:
    product_id: str
    currency: str
    changes: list[PriceChange] = field(default_factory=list)


@dataclass(frozen=True)
class WeekdayRotationRow:
    weekday: int  # 0 = Lunes .. 6 = Domingo
    units: int
    sales_amount: int
    top_product_name: str | None


@dataclass(frozen=True)
class ProductRotation:
    currency: str
    rows: list[WeekdayRotationRow] = field(default_factory=list)
