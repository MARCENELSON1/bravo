"""HMAC-signed, stateless table-QR token.

Same construction as the presence *device* token (``hmac_presence``): a
base64url JSON payload ``{t, tbl, k}`` plus a truncated HMAC-SHA256 signature.
Stateless (no DB) and stable across restarts, so a printed QR keeps resolving.
Unlike the rotating presence code this token does NOT expire — the QR is
physical; expiry/rotation (a table PIN) arrives with ordering/payment (F2/F3)."""

from __future__ import annotations

import base64
import hmac
import json
from hashlib import sha256

from app.domain.public_menu.exceptions import InvalidTableQrToken
from app.domain.public_menu.ports import TableQrToken
from app.domain.public_menu.value_objects import TableQrClaims

_KIND = "table_qr"
_SIG_HEX = 32  # 128 bits


class HmacTableQrToken(TableQrToken):
    def __init__(self, *, secret: str) -> None:
        self._secret = secret.encode()

    def issue(self, tenant_id: str, table_id: str) -> str:
        payload = self._b64(
            json.dumps({"t": tenant_id, "tbl": table_id, "k": _KIND}).encode()
        )
        return f"{payload}.{self._hmac(payload.encode())}"

    def verify(self, token: str) -> TableQrClaims:
        try:
            payload, sig = token.rsplit(".", 1)
            if not hmac.compare_digest(sig, self._hmac(payload.encode())):
                raise InvalidTableQrToken()
            data = json.loads(self._unb64(payload))
            if data.get("k") != _KIND or not data.get("t") or not data.get("tbl"):
                raise InvalidTableQrToken()
            return TableQrClaims(tenant_id=str(data["t"]), table_id=str(data["tbl"]))
        except InvalidTableQrToken:
            raise
        except Exception as exc:  # malformed token
            raise InvalidTableQrToken() from exc

    def _hmac(self, msg: bytes) -> str:
        return hmac.new(self._secret, msg, sha256).hexdigest()[:_SIG_HEX]

    @staticmethod
    def _b64(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    @staticmethod
    def _unb64(value: str) -> bytes:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
