from __future__ import annotations

from enum import StrEnum


class InsightSeverity(StrEnum):
    """How urgent/positive an insight is (drives colour + sort)."""

    GOOD = "GOOD"  # something went well (Bien hecho)
    INFO = "INFO"  # neutral nudge
    WARN = "WARN"  # worth attention
    CRITICAL = "CRITICAL"  # losing money / acute


class InsightBucket(StrEnum):
    """Where the insight surfaces in the advisor UI."""

    TODAY = "TODAY"  # Actuá hoy
    THIS_WEEK = "THIS_WEEK"  # Esta semana
    UPCOMING = "UPCOMING"  # Lo que viene
    WELL_DONE = "WELL_DONE"  # Bien hecho
