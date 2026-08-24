"""payments.tax_amount (Fase 2): sales tax collected within a payment.

Adds ``payments.tax_amount`` (NOT NULL, default 0). It's the sales-tax portion
included in the payment's ``amount`` (a liability owed to the state), separate
from revenue. 0 for existing/AR payments → parity. Mirrors ``tip_amount``.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0041_payment_tax_amount"
down_revision: str | None = "0040_tenant_fiscal_address"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "payments",
        sa.Column("tax_amount", sa.BigInteger(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("payments", "tax_amount")
