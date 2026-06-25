from __future__ import annotations

import pytest

from app.domain.identity.exceptions import InvalidToken
from app.domain.user.value_objects import Role
from app.infrastructure.security.token_service import JwtTokenService


def _svc() -> JwtTokenService:
    return JwtTokenService(secret="test-secret", algorithm="HS256", access_token_ttl_min=15)


def test_stream_token_roundtrips_to_its_tenant() -> None:
    svc = _svc()
    token = svc.create_stream_token(tenant_id="t1", ttl_seconds=60)
    assert svc.decode_stream_token(token) == "t1"


def test_access_token_is_rejected_as_a_stream_token() -> None:
    svc = _svc()
    access = svc.create_access_token(user_id="u1", tenant_id="t1", role=Role.OWNER)
    with pytest.raises(InvalidToken):
        svc.decode_stream_token(access)


def test_stream_token_is_rejected_as_an_access_token() -> None:
    svc = _svc()
    stream = svc.create_stream_token(tenant_id="t1", ttl_seconds=60)
    with pytest.raises(InvalidToken):
        svc.decode_access_token(stream)
