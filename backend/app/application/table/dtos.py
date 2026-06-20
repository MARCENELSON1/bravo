from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateTableResult:
    table_id: str
