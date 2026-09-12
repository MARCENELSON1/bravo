"""Self-service (Fase 3): widen ``orders.source`` to fit CUSTOMER_QR_PREPAID.

The new ``OrderSource.CUSTOMER_QR_PREPAID`` (19 chars) doesn't fit the original
VARCHAR(16). Widen to VARCHAR(32). Data-preserving (only grows the column).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0052_widen_order_source"
down_revision: str | None = "0051_self_order_prepay"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "orders",
        "source",
        existing_type=sa.String(length=16),
        type_=sa.String(length=32),
        existing_nullable=True,
        existing_server_default="WAITER",
    )


def downgrade() -> None:
    op.alter_column(
        "orders",
        "source",
        existing_type=sa.String(length=32),
        type_=sa.String(length=16),
        existing_nullable=True,
        existing_server_default="WAITER",
    )
