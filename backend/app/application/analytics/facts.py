"""Canonical (silver) facts: a normalized, single-shape representation of the
business events the analytics layer reads. Decoupled from how they were captured."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SaleFact:
    """One line of a PAID order. Snapshots the name/category/price at sale time
    and the recipe food cost when the product has one (else None). Integer minor
    units throughout; ``occurred_at`` is the moment the order was settled (PAID)."""

    id: str
    tenant_id: str
    order_id: str
    order_item_id: str
    product_id: str
    product_name: str
    category: str | None
    quantity: int
    unit_price_amount: int
    line_amount: int
    food_cost_amount: int | None  # bruto (COGS a costo real)
    currency: str
    waiter_id: str
    table_id: str | None
    occurred_at: datetime
    created_at: datetime | None = None
    # Netos de IVA congelados en la proyección (Solución 1): base del margen
    # consistente en todas las pantallas (ventas netas − food neto), simétricos y
    # sin re-neteo en lectura. None → se leen como bruto (filas previas / VAT off).
    line_net_amount: int | None = None
    food_cost_net_amount: int | None = None
    # Versión de la receta al momento de la venta (Fase 2D); None = sin receta o
    # fila previa. Es metadata de atribución; no afecta ningún agregado de costo.
    recipe_version: int | None = None
    # Cuánto de ``unit_price_amount`` son adicionales elegidos por el comensal
    # (+panceta, doble queso). El precio unitario los trae ya sumados —una milanesa
    # a $8.000 con panceta de $1.200 se registra a $9.200— y sin esto el mismo plato
    # aparece con precios distintos según lo que cada uno le agregó: el promedio
    # deja de ser comparable con el de la carta y los adicionales, que suelen ser
    # margen alto, no se pueden medir como línea. El precio de carta es
    # ``unit_price_amount − options_amount``. No entra en ningún agregado existente.
    options_amount: int = 0
