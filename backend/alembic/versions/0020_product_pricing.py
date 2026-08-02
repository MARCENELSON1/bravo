"""Productos v2 Tanda B: histórico de precios + inflación mensual estimada.

Tabla nueva ``product_price_changes`` (append-only log de precios por producto)
con RLS, y columna aditiva ``advisor_settings.monthly_inflation_bps`` (default 0)
para calcular "debería estar en $X".

Revision ID: 0020_product_pricing
Revises: 0019_finance_daily_snapshots
Create Date: 2026-07-30
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.infrastructure.persistence.models import Base, ProductPriceChangeORM

revision: str = "0020_product_pricing"
down_revision: str | None = "0019_finance_daily_snapshots"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "bravo_app"
RLS_TABLES = ("product_price_changes",)
_NEW_TABLES = [ProductPriceChangeORM.__table__]


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, tables=_NEW_TABLES)
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP_ROLE};"
    )
    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
                USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
                WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
            """
        )
    op.add_column(
        "advisor_settings",
        sa.Column(
            "monthly_inflation_bps", sa.Integer(), nullable=False, server_default="0"
        ),
    )


def downgrade() -> None:
    op.drop_column("advisor_settings", "monthly_inflation_bps")
    bind = op.get_bind()
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    Base.metadata.drop_all(bind=bind, tables=_NEW_TABLES)
