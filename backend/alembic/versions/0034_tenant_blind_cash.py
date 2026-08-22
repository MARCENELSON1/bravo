"""per-tenant flag: blind cash count (arqueo ciego).

Adds ``tenants.blind_cash_count`` (NOT NULL, default false). OFF for everyone →
the arqueo shows the esperado while counting, as today (parity). Flip it per
tenant so the cashier counts blind (the difference stays honest).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0034_tenant_blind_cash"
down_revision: str | None = "0033_cash_movements"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "blind_cash_count",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("tenants", "blind_cash_count")
