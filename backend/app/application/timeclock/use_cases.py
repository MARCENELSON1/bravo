from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from app.application.clock import utcnow
from app.domain.identity.ports import TenantContext
from app.domain.timeclock.entities import Shift
from app.domain.timeclock.exceptions import NoOpenShift, ShiftAlreadyOpen, ShiftNotFound
from app.domain.timeclock.repository import ShiftRepository
from app.domain.timeclock.value_objects import ShiftSource, ShiftStatus

# How many recent shifts the "my timeclock" view returns.
_RECENT_LIMIT = 20


class ClockIn:
    """Open a shift for the logged-in user. Rejects if one is already open."""

    def __init__(self, shifts: ShiftRepository, tenant_context: TenantContext) -> None:
        self._shifts = shifts
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        user_id: str,
        source: ShiftSource = ShiftSource.SELF,
        note: str | None = None,
    ) -> Shift:
        self._tenant_context.set(tenant_id)
        if await self._shifts.get_open_for_user(tenant_id, user_id) is not None:
            raise ShiftAlreadyOpen()
        shift = Shift(
            id=str(uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            clock_in_at=utcnow(),
            source=source,
            note=note,
        )
        await self._shifts.add(shift)
        return shift


class ClockOut:
    """Close the logged-in user's open shift. Rejects if none is open."""

    def __init__(self, shifts: ShiftRepository, tenant_context: TenantContext) -> None:
        self._shifts = shifts
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, user_id: str) -> Shift:
        self._tenant_context.set(tenant_id)
        shift = await self._shifts.get_open_for_user(tenant_id, user_id)
        if shift is None:
            raise NoOpenShift()
        shift.close(utcnow())
        await self._shifts.save(shift)
        return shift


class Punch:
    """Toggle: open a shift if none is open, otherwise close the open one.

    This is the single-button flow the UI widget uses (and the presence layer
    in T6). Unlike ``ClockIn``/``ClockOut`` it never raises on state — it just
    flips. The ``source`` is recorded on the shift when it is opened.
    """

    def __init__(self, shifts: ShiftRepository, tenant_context: TenantContext) -> None:
        self._shifts = shifts
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, user_id: str, source: ShiftSource = ShiftSource.SELF
    ) -> Shift:
        self._tenant_context.set(tenant_id)
        now = utcnow()
        shift = await self._shifts.get_open_for_user(tenant_id, user_id)
        if shift is None:
            shift = Shift(
                id=str(uuid4()),
                tenant_id=tenant_id,
                user_id=user_id,
                clock_in_at=now,
                source=source,
            )
            await self._shifts.add(shift)
        else:
            shift.close(now)
            await self._shifts.save(shift)
        return shift


@dataclass
class MyTimeclock:
    """The logged-in user's current state: the open shift (if any) + recents."""

    open_shift: Shift | None
    recent: list[Shift]


class GetMyTimeclock:
    def __init__(self, shifts: ShiftRepository, tenant_context: TenantContext) -> None:
        self._shifts = shifts
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, user_id: str) -> MyTimeclock:
        self._tenant_context.set(tenant_id)
        recent = await self._shifts.list(tenant_id, user_id=user_id)
        open_shift = next((s for s in recent if s.status is ShiftStatus.OPEN), None)
        return MyTimeclock(open_shift=open_shift, recent=recent[:_RECENT_LIMIT])


class ListShifts:
    """OWNER/MANAGER: list shifts, optionally filtered by employee/period."""

    def __init__(self, shifts: ShiftRepository, tenant_context: TenantContext) -> None:
        self._shifts = shifts
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        user_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[Shift]:
        self._tenant_context.set(tenant_id)
        return await self._shifts.list(
            tenant_id, user_id=user_id, since=since, until=until
        )


class AdjustShift:
    """OWNER/MANAGER correction: overwrite the times, recording who adjusted it."""

    def __init__(self, shifts: ShiftRepository, tenant_context: TenantContext) -> None:
        self._shifts = shifts
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        shift_id: str,
        clock_in_at: datetime,
        clock_out_at: datetime | None,
        by: str,
    ) -> Shift:
        self._tenant_context.set(tenant_id)
        shift = await self._shifts.get_by_id(tenant_id, shift_id)
        if shift is None:
            raise ShiftNotFound()
        shift.adjust(clock_in_at=clock_in_at, clock_out_at=clock_out_at, by=by)
        await self._shifts.save(shift)
        return shift
