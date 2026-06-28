"""Fase 14 Tanda C: per-item kitchen lifecycle + station routing

Adds the per-item lifecycle (``order_items.status/sent_at/ready_at``) and the
station routing columns (``order_items.station``, ``products.station``). All
additive with server defaults, then backfilled for existing rows:

- item ``status`` is derived from the parent order's status (PAID→SERVED,
  CANCELLED→CANCELLED), so every order's *derived* status stays consistent;
- item ``station`` is taken from its product (defaults KITCHEN);
- ``sent_at`` is seeded from the order's ``created_at`` for already-marched items
  so the KDS can still order them by age.

``order_items`` and ``products`` already have RLS (0002), so the new columns
inherit the existing ``tenant_isolation`` policy — no policy changes needed.

Revision ID: 0012_item_lifecycle_station
Revises: 0011_advisor_settings
Create Date: 2026-06-27
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012_item_lifecycle_station"
down_revision: str | None = "0011_advisor_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- additive columns (server defaults backfill existing rows) ----------
    op.execute(
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS "
        "station varchar(10) NOT NULL DEFAULT 'KITCHEN';"
    )
    op.execute(
        "ALTER TABLE order_items ADD COLUMN IF NOT EXISTS "
        "status varchar(20) NOT NULL DEFAULT 'PENDING';"
    )
    op.execute(
        "ALTER TABLE order_items ADD COLUMN IF NOT EXISTS "
        "station varchar(10) NOT NULL DEFAULT 'KITCHEN';"
    )
    op.execute(
        "ALTER TABLE order_items ADD COLUMN IF NOT EXISTS sent_at timestamptz;"
    )
    op.execute(
        "ALTER TABLE order_items ADD COLUMN IF NOT EXISTS ready_at timestamptz;"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_order_items_status ON order_items (status);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_order_items_station ON order_items (station);"
    )

    # --- backfill existing rows --------------------------------------------
    # Item status mirrors the parent order so the derived order status is stable.
    op.execute(
        """
        UPDATE order_items oi SET status = CASE o.status
            WHEN 'OPEN' THEN 'PENDING'
            WHEN 'SENT' THEN 'SENT'
            WHEN 'PREPARING' THEN 'PREPARING'
            WHEN 'READY' THEN 'READY'
            WHEN 'SERVED' THEN 'SERVED'
            WHEN 'PAID' THEN 'SERVED'
            WHEN 'CANCELLED' THEN 'CANCELLED'
            ELSE 'SERVED'
        END
        FROM orders o
        WHERE oi.order_id = o.id;
        """
    )
    # Station snapshots the product's station (defaults KITCHEN).
    op.execute(
        """
        UPDATE order_items oi SET station = COALESCE(p.station, 'KITCHEN')
        FROM products p
        WHERE oi.product_id = p.id;
        """
    )
    # Already-marched items get a sent_at so the KDS can sort them by age.
    op.execute(
        """
        UPDATE order_items oi SET sent_at = o.created_at
        FROM orders o
        WHERE oi.order_id = o.id
          AND oi.status IN ('SENT', 'PREPARING', 'READY', 'SERVED');
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_order_items_station;")
    op.execute("DROP INDEX IF EXISTS ix_order_items_status;")
    op.execute("ALTER TABLE order_items DROP COLUMN IF EXISTS ready_at;")
    op.execute("ALTER TABLE order_items DROP COLUMN IF EXISTS sent_at;")
    op.execute("ALTER TABLE order_items DROP COLUMN IF EXISTS station;")
    op.execute("ALTER TABLE order_items DROP COLUMN IF EXISTS status;")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS station;")
