from __future__ import annotations

import pytest

from app.domain.public_menu.exceptions import InvalidTableQrToken
from app.infrastructure.public_menu.signed_table_qr import HmacTableQrToken


def _adapter(secret: str = "s3cr3t") -> HmacTableQrToken:
    return HmacTableQrToken(secret=secret)


def test_issue_verify_round_trip() -> None:
    adapter = _adapter()
    token = adapter.issue("t1", "table-9")
    claims = adapter.verify(token)
    assert claims.tenant_id == "t1"
    assert claims.table_id == "table-9"


def test_deterministic_same_inputs_same_token() -> None:
    # A printed QR must stay valid: issuing again yields the exact same token.
    adapter = _adapter()
    assert adapter.issue("t1", "table-9") == adapter.issue("t1", "table-9")


def test_tampered_token_rejected() -> None:
    adapter = _adapter()
    token = adapter.issue("t1", "table-9")
    with pytest.raises(InvalidTableQrToken):
        adapter.verify(token[:-2] + "00")


def test_secret_mismatch_rejected() -> None:
    token = _adapter(secret="one").issue("t1", "table-9")
    with pytest.raises(InvalidTableQrToken):
        _adapter(secret="two").verify(token)


def test_garbage_rejected() -> None:
    with pytest.raises(InvalidTableQrToken):
        _adapter().verify("not-a-token")


def test_wrong_kind_payload_rejected() -> None:
    # A validly-signed token of another kind (e.g. a presence device token shape)
    # must not pass as a table-QR token.
    import base64
    import json

    adapter = _adapter()
    payload = base64.urlsafe_b64encode(
        json.dumps({"t": "t1", "tbl": "table-9", "k": "presence_device"}).encode()
    ).decode().rstrip("=")
    sig = adapter._hmac(payload.encode())  # correctly signed, wrong kind
    with pytest.raises(InvalidTableQrToken):
        adapter.verify(f"{payload}.{sig}")
