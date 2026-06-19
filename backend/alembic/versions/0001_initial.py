"""initial schema + multi-tenant Row Level Security

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-18
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from app.infrastructure.persistence.models import Base

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Dedicated NON-superuser role the application connects with. RLS is only
# enforced for non-owner/non-superuser roles, so this is what makes the
# tenant isolation policies bite. The password is for local dev only.
APP_ROLE = "bravo_app"
APP_ROLE_PASSWORD = "bravo_app"

# Sensitive tenant-scoped tables that get FORCE RLS + an isolation policy.
# Token tables are looked up by their unique high-entropy hash (the capability)
# outside any tenant session, so they are intentionally not RLS-gated.
RLS_TABLES = ("users", "auth_audit")


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                CREATE ROLE {APP_ROLE} LOGIN PASSWORD '{APP_ROLE_PASSWORD}';
            END IF;
        END
        $$;
        """
    )
    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE};")
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP_ROLE};"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {APP_ROLE};"
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
    Base.metadata.drop_all(bind=bind)
    # The application role is intentionally left in place.
