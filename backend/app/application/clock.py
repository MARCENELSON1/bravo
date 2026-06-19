"""Time source for use cases (kept tiny so tests can patch it if needed)."""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(tz=UTC)
