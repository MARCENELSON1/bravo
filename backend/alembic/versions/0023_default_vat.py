"""add advisor_settings.default_vat_bps (IVA neto).

Global VAT rate per tenant in basis points. Defaults to 0 = "not loaded" (netting
off, full parity) — same pattern as monthly_inflation_bps; the owner loads 2100
(21%) to turn netting on. Nets the sale price for margins/ratios and ingredient
costs on purchase.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0023_default_vat"
down_revision: str | None = "0022_ingredient_yield"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "advisor_settings",
        sa.Column("default_vat_bps", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("advisor_settings", "default_vat_bps")
