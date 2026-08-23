"""regional/fiscal spine on tenants (Fase 0 internacionalización).

Adds ``tax_regime``, ``locale``, ``timezone``, ``tax_engine`` to ``tenants``,
all NOT NULL with AR defaults → existing rows backfill to today's behavior
(parity). These feed the per-tenant resolvers (AFIP vs US receipt; TaxJar vs
Avalara). ``country`` and ``currency`` already existed.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0039_tenant_regional_spine"
down_revision: str | None = "0038_supplier_enrichment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("tax_regime", sa.String(20), nullable=False, server_default="AR_AFIP"),
    )
    op.add_column(
        "tenants",
        sa.Column("locale", sa.String(10), nullable=False, server_default="es-AR"),
    )
    op.add_column(
        "tenants",
        sa.Column(
            "timezone",
            sa.String(40),
            nullable=False,
            server_default="America/Argentina/Buenos_Aires",
        ),
    )
    op.add_column(
        "tenants",
        sa.Column("tax_engine", sa.String(20), nullable=False, server_default="NONE"),
    )


def downgrade() -> None:
    op.drop_column("tenants", "tax_engine")
    op.drop_column("tenants", "timezone")
    op.drop_column("tenants", "locale")
    op.drop_column("tenants", "tax_regime")
