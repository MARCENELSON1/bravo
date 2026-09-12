"""self-service (Carta QR F3, Fase 3): per-tenant prepay flag.

Adds ``tenants.self_order_prepay_required`` (default false → every existing tenant
keeps the F2/Fase 2 behaviour: order → waiter confirms → pay at the end). When true
(Self-service mode) a QR order is held off the kitchen until it's paid, and the
payment webhook marches + auto-assigns it. Defaulted → parity for existing tenants.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0051_self_order_prepay"
down_revision: str | None = "0050_payment_idempotency"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "self_order_prepay_required",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("tenants", "self_order_prepay_required")
