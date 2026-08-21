"""per-tenant flag: require an open cash session to charge (guarda B3).

Adds ``tenants.require_open_cash_session`` (NOT NULL, default false). OFF for
everyone → the cobro path is unchanged (parity). Flip it per tenant (by SQL for
now) to enforce blocking a cobro when there is no open cash session.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0029_tenant_require_cash"
down_revision: str | None = "0028_payment_cash_session"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "require_open_cash_session",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("tenants", "require_open_cash_session")
