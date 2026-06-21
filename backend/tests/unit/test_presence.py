from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

import app.infrastructure.timeclock.hmac_presence as hmac_presence
from app.domain.timeclock.exceptions import (
    InvalidPresenceDevice,
    InvalidPresenceToken,
    PresenceRateLimited,
    PresenceTokenReused,
)
from app.domain.timeclock.presence import PresenceUsageStore
from app.infrastructure.timeclock.hmac_presence import HmacPresenceToken


class _FakeStore(PresenceUsageStore):
    def __init__(self, recent: int = 0) -> None:
        self.used: set[tuple[str, int, str]] = set()
        self.recent = recent

    async def count_recent(self, tenant_id, user_id, since):  # noqa: ANN001
        return self.recent

    async def mark_used(self, tenant_id, time_step, user_id):  # noqa: ANN001
        key = (tenant_id, time_step, user_id)
        if key in self.used:
            raise PresenceTokenReused()
        self.used.add(key)


def _adapter(store: _FakeStore, secret: str = "s3cr3t") -> HmacPresenceToken:
    return HmacPresenceToken(store=store, secret=secret, period_seconds=30, rate_max=5)


async def test_verify_accepts_scanned_qr_payload() -> None:
    store = _FakeStore()
    adapter = _adapter(store)
    challenge = adapter.current("t1")
    await adapter.verify("t1", challenge.qr_payload, "u1")  # no raise
    assert len(store.used) == 1


async def test_verify_accepts_typed_code_case_insensitive() -> None:
    adapter = _adapter(_FakeStore())
    challenge = adapter.current("t1")
    await adapter.verify("t1", challenge.code.lower(), "u1")  # no raise


async def test_verify_rejects_garbage() -> None:
    adapter = _adapter(_FakeStore())
    adapter.current("t1")
    with pytest.raises(InvalidPresenceToken):
        await adapter.verify("t1", "NOPE12", "u1")


async def test_verify_rejects_other_tenant_token() -> None:
    adapter = _adapter(_FakeStore())
    challenge = adapter.current("t1")
    with pytest.raises(InvalidPresenceToken):
        await adapter.verify("t2", challenge.qr_payload, "u1")


async def test_replay_by_same_user_rejected() -> None:
    adapter = _adapter(_FakeStore())
    challenge = adapter.current("t1")
    await adapter.verify("t1", challenge.code, "u1")
    with pytest.raises(PresenceTokenReused):
        await adapter.verify("t1", challenge.code, "u1")


async def test_rate_limited_when_too_many_recent() -> None:
    adapter = _adapter(_FakeStore(recent=5))
    challenge = adapter.current("t1")
    with pytest.raises(PresenceRateLimited):
        await adapter.verify("t1", challenge.code, "u1")


async def test_previous_step_still_accepted(monkeypatch) -> None:
    base = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)
    monkeypatch.setattr(hmac_presence, "utcnow", lambda: base)
    adapter = _adapter(_FakeStore())
    challenge = adapter.current("t1")
    # One period later: the token is now the *previous* step → still valid.
    monkeypatch.setattr(hmac_presence, "utcnow", lambda: base + timedelta(seconds=30))
    await adapter.verify("t1", challenge.qr_payload, "u1")  # no raise


async def test_expired_two_steps_later_rejected(monkeypatch) -> None:
    base = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)
    monkeypatch.setattr(hmac_presence, "utcnow", lambda: base)
    adapter = _adapter(_FakeStore())
    challenge = adapter.current("t1")
    monkeypatch.setattr(hmac_presence, "utcnow", lambda: base + timedelta(seconds=75))
    with pytest.raises(InvalidPresenceToken):
        await adapter.verify("t1", challenge.qr_payload, "u1")


def test_device_token_round_trip() -> None:
    adapter = _adapter(_FakeStore())
    token = adapter.issue_device_token("t1")
    assert adapter.device_tenant(token) == "t1"


def test_tampered_device_token_rejected() -> None:
    adapter = _adapter(_FakeStore())
    token = adapter.issue_device_token("t1")
    with pytest.raises(InvalidPresenceDevice):
        adapter.device_tenant(token[:-2] + "00")


def test_device_token_secret_mismatch_rejected() -> None:
    token = _adapter(_FakeStore(), secret="one").issue_device_token("t1")
    with pytest.raises(InvalidPresenceDevice):
        _adapter(_FakeStore(), secret="two").device_tenant(token)
