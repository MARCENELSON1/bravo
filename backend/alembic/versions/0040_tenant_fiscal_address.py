"""tenant fiscal address (Fase 2): point-of-sale address for US sales tax.

Adds nullable ``fiscal_street/city/state/zip`` to ``tenants``. NULL for existing
(AR) tenants → parity; a US tenant sets them so TaxJar can resolve the combined
rate by address. ``country`` already existed.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0040_tenant_fiscal_address"
down_revision: str | None = "0039_tenant_regional_spine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("fiscal_street", sa.String(160), nullable=True))
    op.add_column("tenants", sa.Column("fiscal_city", sa.String(80), nullable=True))
    op.add_column("tenants", sa.Column("fiscal_state", sa.String(40), nullable=True))
    op.add_column("tenants", sa.Column("fiscal_zip", sa.String(16), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "fiscal_zip")
    op.drop_column("tenants", "fiscal_state")
    op.drop_column("tenants", "fiscal_city")
    op.drop_column("tenants", "fiscal_street")
