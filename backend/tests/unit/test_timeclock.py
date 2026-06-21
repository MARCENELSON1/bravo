from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.timeclock.entities import Shift
from app.domain.timeclock.exceptions import InvalidShiftTime, ShiftAlreadyClosed
from app.domain.timeclock.hours import daily_overtime, total_worked_minutes
from app.domain.timeclock.value_objects import ShiftSource, ShiftStatus

_IN = datetime(2026, 6, 21, 9, 0, tzinfo=UTC)


def _open_shift(clock_in: datetime = _IN) -> Shift:
    return Shift(id="s1", tenant_id="t1", user_id="u1", clock_in_at=clock_in)


def test_shift_starts_open() -> None:
    shift = _open_shift()
    assert shift.status is ShiftStatus.OPEN
    assert shift.source is ShiftSource.SELF
    assert shift.worked_minutes is None


def test_shift_close_sets_worked_minutes() -> None:
    shift = _open_shift()
    shift.close(_IN + timedelta(hours=8, minutes=30))
    assert shift.status is ShiftStatus.CLOSED
    assert shift.worked_minutes == 510


def test_shift_close_twice_rejected() -> None:
    shift = _open_shift()
    shift.close(_IN + timedelta(hours=8))
    with pytest.raises(ShiftAlreadyClosed):
        shift.close(_IN + timedelta(hours=9))


def test_shift_close_before_clock_in_rejected() -> None:
    shift = _open_shift()
    with pytest.raises(InvalidShiftTime):
        shift.close(_IN - timedelta(minutes=1))


def test_shift_adjust_records_audit() -> None:
    shift = _open_shift()
    new_in = _IN + timedelta(minutes=5)
    new_out = _IN + timedelta(hours=8)
    shift.adjust(clock_in_at=new_in, clock_out_at=new_out, by="mgr1")
    assert shift.status is ShiftStatus.CLOSED
    assert shift.source is ShiftSource.MANAGER
    assert shift.adjusted_by == "mgr1"
    assert shift.clock_in_at == new_in
    assert shift.clock_out_at == new_out


def test_shift_adjust_can_reopen() -> None:
    shift = _open_shift()
    shift.close(_IN + timedelta(hours=8))
    shift.adjust(clock_in_at=_IN, clock_out_at=None, by="mgr1")
    assert shift.status is ShiftStatus.OPEN
    assert shift.clock_out_at is None


def test_shift_adjust_invalid_time_rejected() -> None:
    shift = _open_shift()
    with pytest.raises(InvalidShiftTime):
        shift.adjust(clock_in_at=_IN, clock_out_at=_IN - timedelta(minutes=1), by="mgr1")


def test_daily_overtime_under_standard_is_zero() -> None:
    assert daily_overtime(480, 480) == 0
    assert daily_overtime(420, 480) == 0


def test_daily_overtime_over_standard() -> None:
    assert daily_overtime(510, 480) == 30  # 8.5h → 30 min
    assert daily_overtime(600, 480) == 120  # turno cortado 5+5 → 2h


def test_total_worked_minutes_sums_closed_ignores_open() -> None:
    morning = _open_shift(_IN)
    morning.close(_IN + timedelta(hours=5))
    afternoon = _open_shift(_IN + timedelta(hours=6))
    afternoon.close(_IN + timedelta(hours=11))
    still_open = _open_shift(_IN + timedelta(hours=12))
    assert total_worked_minutes([morning, afternoon, still_open]) == 600
