from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.domain.identity.exceptions import ExpiredToken, InvalidToken
from app.domain.identity.ports import TokenService
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role


class JwtTokenService(TokenService):
    """Access tokens are HS256 JWTs; opaque tokens are ``{tenant_id}.{secret}``
    and only their SHA-256 hash is stored server-side."""

    _ISSUER = "bravo-api"
    _AUDIENCE = "bravo-api"

    def __init__(self, secret: str, algorithm: str, access_token_ttl_min: int) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._access_token_ttl_min = access_token_ttl_min

    def create_access_token(self, *, user_id: str, tenant_id: str, role: Role) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "role": str(role),
            "type": "access",
            "iss": self._ISSUER,
            "aud": self._AUDIENCE,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self._access_token_ttl_min)).timestamp()),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> AccessClaims:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                audience=self._AUDIENCE,
                issuer=self._ISSUER,
                options={"require": ["exp", "iat", "sub", "type"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise ExpiredToken() from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidToken() from exc
        if payload.get("type") != "access":
            raise InvalidToken()
        try:
            return AccessClaims(
                user_id=payload["sub"],
                tenant_id=payload["tenant_id"],
                role=Role(payload["role"]),
            )
        except (KeyError, ValueError) as exc:
            raise InvalidToken() from exc

    def generate_opaque_token(self, tenant_id: str) -> str:
        return f"{tenant_id}.{secrets.token_urlsafe(32)}"

    def read_tenant(self, token: str) -> str:
        prefix, sep, _ = token.partition(".")
        if not sep or not prefix:
            raise InvalidToken()
        try:
            UUID(prefix)
        except ValueError as exc:
            raise InvalidToken() from exc
        return prefix

    def hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def verify_token(self, token: str, token_hash: str) -> bool:
        return hmac.compare_digest(self.hash_token(token), token_hash)
