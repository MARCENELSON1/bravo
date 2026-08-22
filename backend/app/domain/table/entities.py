from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Table:
    """A physical table, scoped to a tenant."""

    id: str
    tenant_id: str
    number: int
    name: str | None = None
    active: bool = True
    # table_sessions (cimiento): zona del salón y capacidad (para el default de PAX).
    # Nullable → paridad (sin sector = tablero plano; sin capacity = sin default).
    sector_id: str | None = None
    capacity: int | None = None
    created_at: datetime | None = None
