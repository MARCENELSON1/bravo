"""add frozen net-of-VAT columns for sales and food cost (Solución 1).

Freeze BOTH the net-of-VAT sales and the per-ingredient net food cost at
projection time, so every aggregate margin read model compares like-with-like
(frozen net sales − frozen net food) with no read-time re-netting — symmetric,
and immune to a later VAT-rate change re-netting one side but not the other.

- ``sale_facts.line_net_amount`` / ``food_cost_net_amount`` — nullable; old rows
  read as gross via COALESCE. Backfilled to the gross value here (net == gross
  when no VAT was in effect, which is exactly the pre-migration history).
- ``finance_daily_snapshots.sales_net_amount`` / ``food_cost_net_amount`` —
  server_default "0" (aggregate maintained incrementally); backfilled to the
  gross daily totals so pre-migration snapshot days don't read net as 0.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0025_food_cost_net"
down_revision: str | None = "0024_cost_includes_tax"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sale_facts",
        sa.Column("line_net_amount", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "sale_facts",
        sa.Column("food_cost_net_amount", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "finance_daily_snapshots",
        sa.Column(
            "sales_net_amount", sa.BigInteger(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "finance_daily_snapshots",
        sa.Column(
            "food_cost_net_amount", sa.BigInteger(), nullable=False, server_default="0"
        ),
    )
    # Backfill: pre-migration rows had no VAT in effect → net == gross.
    op.execute("UPDATE sale_facts SET line_net_amount = line_amount")
    op.execute(
        "UPDATE sale_facts SET food_cost_net_amount = food_cost_amount "
        "WHERE food_cost_amount IS NOT NULL"
    )
    op.execute("UPDATE finance_daily_snapshots SET sales_net_amount = sales_amount")
    op.execute(
        "UPDATE finance_daily_snapshots SET food_cost_net_amount = food_cost_amount"
    )


def downgrade() -> None:
    op.drop_column("finance_daily_snapshots", "food_cost_net_amount")
    op.drop_column("finance_daily_snapshots", "sales_net_amount")
    op.drop_column("sale_facts", "food_cost_net_amount")
    op.drop_column("sale_facts", "line_net_amount")
