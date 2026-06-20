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
    created_at: datetime | None = None
