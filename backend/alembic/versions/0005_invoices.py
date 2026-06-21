"""Fase 4: facturación electrónica (invoices + tax_credentials) + RLS

Revision ID: 0005_invoices
Revises: 0004_payment_credentials
Create Date: 2026-06-21
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from app.infrastructure.persistence.models import Base, InvoiceORM, TaxCredentialORM

# revision identifiers, used by Alembic.
revision: str = "0005_invoices"
down_revision: str | None = "0004_payment_credentials"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "bravo_app"
RLS_TABLES = ("invoices", "tax_credentials")
_NEW_TABLES = [InvoiceORM.__table__, TaxCredentialORM.__table__]


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


def downgrade() -> None:
    bind = op.get_bind()
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    Base.metadata.drop_all(bind=bind, tables=_NEW_TABLES)
