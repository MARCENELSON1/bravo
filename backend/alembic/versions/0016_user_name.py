"""Identidad Wellnod: nombre de la persona en users (para el saludo del dashboard
y las iniciales del avatar). Columna additiva, opcional — se captura en el
onboarding; los usuarios existentes quedan en NULL y la UI degrada con gracia.

Revision ID: 0016_user_name
Revises: 0015_advisor_diagnostics
Create Date: 2026-07-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_user_name"
down_revision: str | None = "0015_advisor_diagnostics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(120), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "name")
