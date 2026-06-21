from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.timeclock.exceptions import InvalidShiftTime, ShiftAlreadyClosed
from app.domain.timeclock.value_objects import ShiftSource, ShiftStatus


@dataclass
class Shift:
    """A worked shift (turno) for a user, scoped to a tenant.

    A shift opens when the worker clocks in and closes when they clock out.
    Several shifts per day are valid (turno cortado): the day total is the sum
    of the closed shifts. Timestamps are always set by the server.
    """

    id: str
    tenant_id: str
    user_id: str
    clock_in_at: datetime
    clock_out_at: datetime | None = None
    status: ShiftStatus = ShiftStatus.OPEN
    source: ShiftSource = ShiftSource.SELF
    note: str | None = None
    adjusted_by: str | None = None
    created_at: datetime | None = None

    def close(self, at: datetime) -> None:
        if self.status is ShiftStatus.CLOSED:
            raise ShiftAlreadyClosed()
        if at < self.clock_in_at:
            raise InvalidShiftTime()
        self.clock_out_at = at
        self.status = ShiftStatus.CLOSED

    def adjust(self, *, clock_in_at: datetime, clock_out_at: datetime | None, by: str) -> None:
        """Manager correction: overwrite the times and record who adjusted it."""
        if clock_out_at is not None and clock_out_at < clock_in_at:
            raise InvalidShiftTime()
        self.clock_in_at = clock_in_at
        self.clock_out_at = clock_out_at
        self.status = ShiftStatus.CLOSED if clock_out_at is not None else ShiftStatus.OPEN
        self.source = ShiftSource.MANAGER
        self.adjusted_by = by

    @property
    def worked_minutes(self) -> int | None:
        """Minutes between clock-in and clock-out, or None while still open."""
        if self.clock_out_at is None:
            return None
        return int((self.clock_out_at - self.clock_in_at).total_seconds() // 60)
