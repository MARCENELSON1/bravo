"""link payments to their cash session (guarda B, fase 1).

Adds a nullable ``payments.cash_session_id`` so every cobro records the open cash
session at charge time. Backfills historical payments by matching their
``created_at`` to each session's open window ``[opened_at, closed_at)`` (at most
one, since only one cash session is open at a time). No enforcement yet — blocking
a cobro without an open cash session is a later phase behind a per-tenant flag →
invisible / parity.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0028_payment_cash_session"
down_revision: str | None = "0027_recipe_version"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "payments",
        sa.Column("cash_session_id", sa.Uuid(as_uuid=False), nullable=True),
    )
    op.create_index("ix_payments_cash_session_id", "payments", ["cash_session_id"])
    # Backfill: cada pago cae en la caja de su tenant cuya ventana [opened, closed)
    # lo contiene. Idempotente (solo toca los NULL). Los pagos de tenants que nunca
    # abrieron caja quedan NULL — correcto.
    op.execute(
        """
        UPDATE payments p
        SET cash_session_id = cs.id
        FROM cash_sessions cs
        WHERE cs.tenant_id = p.tenant_id
          AND p.created_at >= cs.opened_at
          AND p.created_at < COALESCE(cs.closed_at, now())
          AND p.cash_session_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_payments_cash_session_id", table_name="payments")
    op.drop_column("payments", "cash_session_id")
