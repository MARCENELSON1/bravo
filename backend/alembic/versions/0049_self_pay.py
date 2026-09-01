"""pay-from-the-table (Carta QR F3): per-tenant self-pay gate flags.

Adds two ``tenants`` flags: ``self_pay_enabled`` (default false → the QR menu keeps
the F1/F2 "call waiter"/"request bill" behaviour, no online pay, parity) and
``self_pay_tips_enabled`` (default true → the pay screen offers a tip unless the
owner switches it off). Both defaulted → every existing tenant behaves exactly as
before.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0049_self_pay"
down_revision: str | None = "0048_product_modifiers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "self_pay_enabled", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "tenants",
        sa.Column(
            "self_pay_tips_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )


def downgrade() -> None:
    op.drop_column("tenants", "self_pay_tips_enabled")
    op.drop_column("tenants", "self_pay_enabled")
