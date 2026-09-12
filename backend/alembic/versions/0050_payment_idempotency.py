"""pay-from-the-table (Carta QR F3): idempotency key on payments.

Adds ``payments.idempotency_key`` (nullable, indexed): the client sends it per
cobro intent so a double-tapped online charge from the diner replays the existing
payment instead of creating a second one. NULL for every existing/cashier payment
→ parity.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0050_payment_idempotency"
down_revision: str | None = "0049_self_pay"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "payments",
        sa.Column("idempotency_key", sa.String(length=80), nullable=True),
    )
    op.create_index(
        "ix_payments_idempotency_key", "payments", ["idempotency_key"]
    )


def downgrade() -> None:
    op.drop_index("ix_payments_idempotency_key", table_name="payments")
    op.drop_column("payments", "idempotency_key")
