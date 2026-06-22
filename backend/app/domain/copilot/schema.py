"""Curated, read-only allow-list of tables/columns the copilot may query — the
ONLY surface the LLM knows about. NEVER includes users, tokens, *_credentials,
auth_audit, cost settings or system catalogs. Every table is tenant-scoped (RLS).
Column names match the ORM; comparisons are case-insensitive."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TableSpec:
    description: str
    columns: tuple[str, ...]


_SCHEMA: dict[str, TableSpec] = {
    "sale_facts": TableSpec(
        "Una fila por línea de comanda PAGADA (ventas, canónico).",
        (
            "tenant_id", "order_id", "product_id", "product_name", "category",
            "quantity", "unit_price_amount", "line_amount", "food_cost_amount",
            "currency", "waiter_id", "table_id", "occurred_at",
        ),
    ),
    "payments": TableSpec(
        "Cobros (direction=INFLOW) y egresos (direction=OUTFLOW).",
        (
            "tenant_id", "direction", "amount", "currency", "method", "status",
            "order_id", "category", "counterparty", "created_at",
        ),
    ),
    "reservations": TableSpec(
        "Reservas de mesa (status: PENDING/CONFIRMED/SEATED/COMPLETED/CANCELLED/NO_SHOW).",
        (
            "tenant_id", "customer_name", "party_size", "reserved_at", "turn",
            "table_id", "status",
        ),
    ),
    "products": TableSpec(
        "Catálogo de productos.",
        ("tenant_id", "id", "name", "price_amount", "price_currency", "category", "active"),
    ),
    "tables": TableSpec(
        "Mesas del salón.",
        ("tenant_id", "id", "number", "name", "active"),
    ),
    "ingredients": TableSpec(
        "Insumos / stock (cantidades en milésimas de la unidad base).",
        (
            "tenant_id", "id", "name", "unit", "stock_qty", "min_qty",
            "unit_cost_amount", "unit_cost_currency", "active",
        ),
    ),
    "orders": TableSpec(
        "Comandas (status: OPEN/SENT/PREPARING/READY/SERVED/PAID/CANCELLED).",
        ("tenant_id", "id", "table_id", "waiter_id", "status", "currency", "created_at"),
    ),
    "order_items": TableSpec(
        "Ítems de cada comanda.",
        ("tenant_id", "order_id", "product_id", "name", "unit_price_amount", "quantity"),
    ),
    "shifts": TableSpec(
        "Fichajes de empleados (turnos).",
        ("tenant_id", "user_id", "clock_in_at", "clock_out_at", "status", "source"),
    ),
    "invoices": TableSpec(
        "Comprobantes AFIP emitidos.",
        (
            "tenant_id", "type", "point_of_sale", "number", "total_amount",
            "net_amount", "vat_amount", "currency", "status", "issued_at",
        ),
    ),
}

ALLOWED_TABLES = frozenset(_SCHEMA)


def is_allowed_table(table: str) -> bool:
    return table.lower() in _SCHEMA


def allowed_columns(table: str) -> frozenset[str]:
    spec = _SCHEMA.get(table.lower())
    return frozenset(c.lower() for c in spec.columns) if spec is not None else frozenset()


def schema_doc() -> str:
    """Human/LLM-readable description of the queryable schema (for the prompt)."""
    lines: list[str] = []
    for name, spec in _SCHEMA.items():
        lines.append(f"- {name} ({spec.description}): {', '.join(spec.columns)}")
    return "\n".join(lines)
