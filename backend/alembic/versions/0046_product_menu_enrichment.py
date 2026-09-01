"""product menu enrichment (Carta QR F2): image, description, daily availability.

Adds ``products.image_url`` (nullable), ``products.description`` (nullable) and
``products.available_today`` (NOT NULL, default true). All defaulted/nullable →
every existing product behaves exactly as before (parity): no photo/description
and available. ``available_today`` is the "86'd" daily toggle, distinct from
``active`` (a permanent delisting).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0046_product_menu_enrichment"
down_revision: str | None = "0045_user_platform_admin"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("products", sa.Column("image_url", sa.String(length=2048), nullable=True))
    op.add_column("products", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "products",
        sa.Column("available_today", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_column("products", "available_today")
    op.drop_column("products", "description")
    op.drop_column("products", "image_url")
