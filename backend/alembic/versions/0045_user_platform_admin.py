"""Panel de plataforma: flag de super-admin en el usuario.

Agrega ``users.platform_admin`` (bool, default false). El super-admin gestiona el
catálogo global de planes del SaaS; el primer admin se prende con el script de
bootstrap (``app/scripts/promote_platform_admin.py``).

Revision ID: 0045_user_platform_admin
Revises: 0044_billing
Create Date: 2026-08-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0045_user_platform_admin"
down_revision: str | None = "0044_billing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "platform_admin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "platform_admin")
