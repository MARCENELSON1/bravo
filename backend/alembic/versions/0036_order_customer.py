"""order → customer link (CRM historial de compras).

Adds ``orders.customer_id`` (nullable, indexed). NULL → la comanda no está
atribuida a ningún cliente (paridad; nada se infla). Se setea al cobrar/atribuir.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0036_order_customer"
down_revision: str | None = "0035_customers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("customer_id", sa.Uuid(as_uuid=False), nullable=True),
    )
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])


def downgrade() -> None:
    op.drop_index("ix_orders_customer_id", table_name="orders")
    op.drop_column("orders", "customer_id")
