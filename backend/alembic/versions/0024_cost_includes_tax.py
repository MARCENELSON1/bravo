"""add ingredients.cost_includes_tax (IVA neto — check por-compra).

Whether an ingredient's loaded cost includes VAT (responsable inscripto → net it)
or is already net (monotributo/no-VAT supplier). Defaults to true (the common
case). Only matters when the tenant's default_vat_bps is set.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0024_cost_includes_tax"
down_revision: str | None = "0023_default_vat"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ingredients",
        sa.Column(
            "cost_includes_tax",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column("ingredients", "cost_includes_tax")
