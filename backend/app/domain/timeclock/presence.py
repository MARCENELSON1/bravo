"""Proof-of-presence layer (optional, behind a port): a local display shows a
rotating QR + short code; a worker presents the scanned/typed token, which is
verified before delegating to the normal toggle. The token proves *presence*,
never identity — the punch still belongs to the logged-in user."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PresenceChallenge:
    """What the display renders: a QR payload + a short typeable code (both
    encode the same rotating token), valid until ``expires_at``."""

    qr_payload: str
    code: str
    expires_at: datetime


class PresenceToken(ABC):
    """Port for the rotating presence token."""

    @abstractmethod
    def current(self, tenant_id: str) -> PresenceChallenge:
        """The challenge for the current time step (pure; no I/O)."""

    @abstractmethod
    async def verify(self, tenant_id: str, presented: str, user_id: str) -> None:
        """Validate a presented token (signature + time window + single-use per
        ``(token, user)`` + rate-limit). Raises a presence exception otherwise."""

    @abstractmethod
    def issue_device_token(self, tenant_id: str) -> str:
        """Mint a signed device credential for a local display (provisioned by
        the OWNER), so the rotating QR can't be obtained remotely."""

    @abstractmethod
    def device_tenant(self, device_token: str) -> str:
        """Resolve the tenant from a device token; raise if invalid."""


class PresenceUsageStore(ABC):
    """Single-use + rate-limit backing store for presented tokens."""

    @abstractmethod
    async def count_recent(self, tenant_id: str, user_id: str, since: datetime) -> int: ...

    @abstractmethod
    async def mark_used(self, tenant_id: str, time_step: int, user_id: str) -> None:
        """Record a token as consumed by a user; raise ``PresenceTokenReused`` if
        that ``(tenant, time_step, user)`` was already used."""
