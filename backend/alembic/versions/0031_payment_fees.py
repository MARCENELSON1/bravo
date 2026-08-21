"""payment commission foundation (comisiones slice A).

Congela por cobro la comisión de la pasarela: ``payments.fee_amount`` + el neto que
queda (``payments.net_amount``, nullable → COALESCE a amount para históricos), y una
tabla ``payment_fee_rates`` (RLS) con la tasa por método por tenant. Sin filas → 0 →
net == amount → paridad total.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.infrastructure.persistence.models import Base, PaymentFeeRateORM

revision: str = "0031_payment_fees"
down_revision: str | None = "0030_tip_payouts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "bravo_app"
RLS_TABLES = ("payment_fee_rates",)
_NEW_TABLES = [PaymentFeeRateORM.__table__]


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        "payments",
        sa.Column("fee_amount", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.add_column("payments", sa.Column("net_amount", sa.BigInteger(), nullable=True))
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
    op.drop_column("payments", "net_amount")
    op.drop_column("payments", "fee_amount")
