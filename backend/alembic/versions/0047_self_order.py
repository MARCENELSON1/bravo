"""self-order (Carta QR F2): order source + per-tenant self-order gate flags.

Adds ``orders.source`` (default WAITER) to distinguish waiter- vs customer-QR
orders, and two ``tenants`` flags: ``self_order_enabled`` (default false → the QR
menu stays read-only, parity) and ``self_order_requires_confirmation`` (default
true → the kitchen gate is ON: the waiter confirms a customer order). All
defaulted → every existing order/tenant behaves exactly as before.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0047_self_order"
down_revision: str | None = "0046_product_menu_enrichment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("source", sa.String(length=16), nullable=False, server_default="WAITER"),
    )
    op.add_column(
        "tenants",
        sa.Column(
            "self_order_enabled", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "tenants",
        sa.Column(
            "self_order_requires_confirmation",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )


def downgrade() -> None:
    op.drop_column("tenants", "self_order_requires_confirmation")
    op.drop_column("tenants", "self_order_enabled")
    op.drop_column("orders", "source")
