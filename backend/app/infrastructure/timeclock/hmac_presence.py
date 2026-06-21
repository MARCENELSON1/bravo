"""HMAC-based rotating presence token (TOTP-style).

The token for a time step is ``HMAC(secret, "{tenant}:{device}:{step}")`` with
``step = floor(now / period)`` (period ≤ 60 s). The QR carries the full hex
signature; the short code is a base32 prefix of the same signature, so the
typed code and the scanned QR are interchangeable. ``verify`` accepts the
current and previous step (clock skew), is single-use per ``(token, user)`` and
rate-limited. Device tokens are stateless, signed credentials (no DB)."""

from __future__ import annotations

import base64
import hmac
import json
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from app.application.clock import utcnow
from app.domain.timeclock.exceptions import (
    InvalidPresenceDevice,
    InvalidPresenceToken,
    PresenceRateLimited,
)
from app.domain.timeclock.presence import (
    PresenceChallenge,
    PresenceToken,
    PresenceUsageStore,
)

# Single logical fichaje device per tenant for the MVP (multiple displays may
# share one device token). Per-device registration is a future increment.
_DEVICE = "local"
_CODE_LEN = 6
_SIG_HEX = 32  # 128 bits carried in the QR payload


class HmacPresenceToken(PresenceToken):
    def __init__(
        self,
        *,
        store: PresenceUsageStore,
        secret: str,
        period_seconds: int = 30,
        rate_max: int = 10,
        rate_window_seconds: int = 60,
    ) -> None:
        self._store = store
        self._secret = secret.encode()
        self._period = period_seconds
        self._rate_max = rate_max
        self._rate_window = rate_window_seconds

    def current(self, tenant_id: str) -> PresenceChallenge:
        now = utcnow()
        step = self._step(now)
        sig = self._sig(tenant_id, step)
        expires_at = datetime.fromtimestamp((step + 1) * self._period, tz=UTC)
        return PresenceChallenge(
            qr_payload=self._qr(step, sig),
            code=self._code(sig),
            expires_at=expires_at,
        )

    async def verify(self, tenant_id: str, presented: str, user_id: str) -> None:
        presented = presented.strip()
        # Rate-limit first (cheapest gate) before any token work.
        since = utcnow() - timedelta(seconds=self._rate_window)
        if await self._store.count_recent(tenant_id, user_id, since) >= self._rate_max:
            raise PresenceRateLimited()
        current = self._step(utcnow())
        for step in (current, current - 1):
            sig = self._sig(tenant_id, step)
            if self._matches(presented, step, sig):
                # raises PresenceTokenReused if this user already used this step
                await self._store.mark_used(tenant_id, step, user_id)
                return
        raise InvalidPresenceToken()

    def issue_device_token(self, tenant_id: str) -> str:
        payload = self._b64(json.dumps({"t": tenant_id, "k": "presence_device"}).encode())
        return f"{payload}.{self._hmac(payload.encode())}"

    def device_tenant(self, device_token: str) -> str:
        try:
            payload, sig = device_token.rsplit(".", 1)
            if not hmac.compare_digest(sig, self._hmac(payload.encode())):
                raise InvalidPresenceDevice()
            data = json.loads(self._unb64(payload))
            if data.get("k") != "presence_device" or not data.get("t"):
                raise InvalidPresenceDevice()
            return str(data["t"])
        except InvalidPresenceDevice:
            raise
        except Exception as exc:  # malformed token
            raise InvalidPresenceDevice() from exc

    # --- helpers ---
    def _step(self, now: datetime) -> int:
        return int(now.timestamp()) // self._period

    def _sig(self, tenant_id: str, step: int) -> bytes:
        return hmac.new(self._secret, f"{tenant_id}:{_DEVICE}:{step}".encode(), sha256).digest()

    def _hmac(self, msg: bytes) -> str:
        return hmac.new(self._secret, msg, sha256).hexdigest()[:_SIG_HEX]

    def _qr(self, step: int, sig: bytes) -> str:
        return f"{step}.{sig.hex()[:_SIG_HEX]}"

    def _code(self, sig: bytes) -> str:
        return base64.b32encode(sig).decode().replace("=", "")[:_CODE_LEN]

    def _matches(self, presented: str, step: int, sig: bytes) -> bool:
        if "." in presented:
            head, _, tail = presented.partition(".")
            if not head.isdigit() or int(head) != step:
                return False
            return hmac.compare_digest(tail.lower(), sig.hex()[:_SIG_HEX])
        return hmac.compare_digest(presented.upper(), self._code(sig))

    @staticmethod
    def _b64(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    @staticmethod
    def _unb64(value: str) -> bytes:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
