"""add ingredients.yield_pct (merma / rendimiento).

Yield in basis points (10000 = 100% = no loss). Existing rows default to 100%,
so the effective cost — and every food-cost number already in prod — is unchanged.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0022_ingredient_yield"
down_revision: str | None = "0021_preparations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ingredients",
        sa.Column("yield_pct", sa.Integer(), nullable=False, server_default="10000"),
    )


def downgrade() -> None:
    op.drop_column("ingredients", "yield_pct")
