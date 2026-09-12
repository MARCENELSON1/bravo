"""Índices de la ruta caliente (salón, cobro y finanzas).

Cuatro índices compuestos que hoy no existen y que sostienen las consultas que
más se repiten. Sin ellos, Postgres resuelve el filtro por estado/fecha
recorriendo el índice de ``tenant_id`` entero: el costo crece con el historial
del tenant en vez de con lo que la consulta realmente necesita (las mesas
abiertas, el día pedido). Es invisible con poca data y se degrada mes a mes.

- ``orders (tenant_id, status)``: el plano y el KDS piden las comandas activas.
- ``table_sessions``: índice **parcial** sobre las sesiones abiertas — la tabla
  acumula una fila por visita, pero la parte "abierta" siempre es chica.
- ``payments (tenant_id, status, created_at DESC)``: Finanzas/Home ordenan por
  fecha filtrando por estado confirmado.
- ``sale_facts (tenant_id, occurred_at)``: el motor de Finanzas en modo ``live``.

Solo agrega índices: no toca datos ni esquema, y el downgrade los borra.

Revision ID: 0055_hot_path_indexes
Revises: 0054_service_courses
Create Date: 2026-09-05
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0055_hot_path_indexes"
down_revision: str | None = "0054_service_courses"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_orders_tenant_status", "orders", ["tenant_id", "status"])
    # Parcial: el índice queda del tamaño de las mesas abiertas, no del histórico.
    op.create_index(
        "ix_table_sessions_tenant_open",
        "table_sessions",
        ["tenant_id", "opened_at"],
        postgresql_where="closed_at IS NULL AND merged_into_id IS NULL",
    )
    op.create_index(
        "ix_payments_tenant_status_created",
        "payments",
        ["tenant_id", "status", "created_at"],
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "ix_sale_facts_tenant_occurred", "sale_facts", ["tenant_id", "occurred_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_sale_facts_tenant_occurred", table_name="sale_facts")
    op.drop_index("ix_payments_tenant_status_created", table_name="payments")
    op.drop_index("ix_table_sessions_tenant_open", table_name="table_sessions")
    op.drop_index("ix_orders_tenant_status", table_name="orders")
