"""Presence use cases (Fase 5.5): provision a display device, serve the current
challenge to that display, and punch by presenting the scanned/typed token.
Identity stays the logged-in user; the token only proves physical presence."""

from __future__ import annotations

from app.application.timeclock.use_cases import Punch
from app.domain.identity.ports import TenantContext
from app.domain.timeclock.entities import Shift
from app.domain.timeclock.presence import PresenceChallenge, PresenceToken
from app.domain.timeclock.value_objects import ShiftSource


class RegisterPresenceDevice:
    """OWNER provisions a local display: returns a signed device token the
    display stores and uses to fetch the rotating challenge."""

    def __init__(self, presence: PresenceToken, tenant_context: TenantContext) -> None:
        self._presence = presence
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> str:
        self._tenant_context.set(tenant_id)
        return self._presence.issue_device_token(tenant_id)


class GetPresenceChallenge:
    """Display endpoint (device-authenticated, no user session): the current
    QR + code. Read-only and stateless — no tenant DB scope needed."""

    def __init__(self, presence: PresenceToken) -> None:
        self._presence = presence

    async def execute(self, *, device_token: str) -> PresenceChallenge:
        tenant_id = self._presence.device_tenant(device_token)
        return self._presence.current(tenant_id)


class PunchWithPresence:
    """Verify a presented token, then toggle the logged-in user's shift with
    ``source=PRESENCE``."""

    def __init__(
        self, presence: PresenceToken, punch: Punch, tenant_context: TenantContext
    ) -> None:
        self._presence = presence
        self._punch = punch
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, user_id: str, presented: str) -> Shift:
        self._tenant_context.set(tenant_id)
        await self._presence.verify(tenant_id, presented, user_id)
        return await self._punch.execute(
            tenant_id=tenant_id, user_id=user_id, source=ShiftSource.PRESENCE
        )
