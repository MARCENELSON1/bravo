"""Fase 14 Tanda E: propina (tip) en pagos

Adds ``payments.tip_amount`` (minor units, NOT NULL DEFAULT 0) so a cobro can
carry a propina on top of the sale ``amount``. Additive — existing rows backfill
to 0. The tip is never revenue (it stays out of sale_facts); it only feeds the
cash arqueo (a CASH tip is physically in the drawer). ``payments`` keeps its
existing RLS policy — the new column inherits it, no policy change.

Revision ID: 0014_payment_tip
Revises: 0013_cash_sessions
Create Date: 2026-06-28
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0014_payment_tip"
down_revision: str | None = "0013_cash_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS "
        "tip_amount bigint NOT NULL DEFAULT 0;"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS tip_amount;")
