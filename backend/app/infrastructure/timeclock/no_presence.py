"""Disabled presence provider (Selector ``off``): every operation reports that
the presence layer is not enabled for this deployment."""

from __future__ import annotations

from app.domain.timeclock.exceptions import PresenceDisabled
from app.domain.timeclock.presence import PresenceChallenge, PresenceToken


class NoPresence(PresenceToken):
    def current(self, tenant_id: str) -> PresenceChallenge:
        raise PresenceDisabled()

    async def verify(self, tenant_id: str, presented: str, user_id: str) -> None:
        raise PresenceDisabled()

    def issue_device_token(self, tenant_id: str) -> str:
        raise PresenceDisabled()

    def device_tenant(self, device_token: str) -> str:
        raise PresenceDisabled()
