"""Pantalla Finanzas Tanda E: asientos y horario para RevPASH.

``advisor_settings.seats`` (capacidad total del local) y ``daily_open_minutes``
(minutos abiertos por día) — inputs de RevPASH = ventas / (asientos × horas × días).
Additivas y con default 0 (RevPASH degrada a 0 hasta que se carguen).

Revision ID: 0018_advisor_seats_hours
Revises: 0017_user_hourly_rate
Create Date: 2026-07-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018_advisor_seats_hours"
down_revision: str | None = "0017_user_hourly_rate"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "advisor_settings",
        sa.Column("seats", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "advisor_settings",
        sa.Column("daily_open_minutes", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("advisor_settings", "daily_open_minutes")
    op.drop_column("advisor_settings", "seats")
