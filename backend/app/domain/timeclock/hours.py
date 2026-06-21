"""Pure hours math (no I/O): aggregate worked minutes and compute daily
overtime against the tenant's configured standard workday."""

from __future__ import annotations

from app.domain.timeclock.entities import Shift


def total_worked_minutes(shifts: list[Shift]) -> int:
    """Sum the worked minutes of the CLOSED shifts (open ones don't count yet)."""
    return sum(s.worked_minutes or 0 for s in shifts if s.worked_minutes is not None)


def daily_overtime(minutes_in_day: int, standard_workday_minutes: int) -> int:
    """Overtime for a single day = minutes worked beyond the standard workday.

    Always computed over the day total, never per shift: a turno cortado of
    5h + 5h is 10h, so against an 8h standard it yields 2h of overtime.
    """
    return max(0, minutes_in_day - standard_workday_minutes)
