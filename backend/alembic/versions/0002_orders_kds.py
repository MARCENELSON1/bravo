"""Fase 2: comandas (tables, products, orders, order_items) + tenant country/currency + RLS

Revision ID: 0002_orders_kds
Revises: 0001_initial
Create Date: 2026-06-20
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from app.infrastructure.persistence.models import (
    Base,
    OrderItemORM,
    OrderORM,
    ProductORM,
    TableORM,
)

# revision identifiers, used by Alembic.
revision: str = "0002_orders_kds"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "bravo_app"
RLS_TABLES = ("tables", "products", "orders", "order_items")
_NEW_TABLES = [
    TableORM.__table__,
    ProductORM.__table__,
    OrderORM.__table__,
    OrderItemORM.__table__,
]


def upgrade() -> None:
    bind = op.get_bind()

    # Tenant gets a country + currency (default Argentina/ARS).
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS country varchar(2) NOT NULL DEFAULT 'AR';")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS currency varchar(3) NOT NULL DEFAULT 'ARS';")

    Base.metadata.create_all(bind=bind, tables=_NEW_TABLES)

    # Re-assert grants for the app role on the new tables (idempotent).
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


def downgrade() -> None:
    bind = op.get_bind()
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    Base.metadata.drop_all(bind=bind, tables=_NEW_TABLES)
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS currency;")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS country;")
