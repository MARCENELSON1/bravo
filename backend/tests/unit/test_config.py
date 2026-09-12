from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "from-env-secret")
    monkeypatch.setenv("MAX_LOGIN_ATTEMPTS", "9")
    settings = Settings(_env_file=None)
    assert settings.jwt_secret == "from-env-secret"
    assert settings.max_login_attempts == 9
    assert settings.jwt_alg == "HS256"


def test_settings_defaults():
    settings = Settings(_env_file=None)
    assert settings.access_token_ttl_min == 15
    assert settings.email_transport in {"console", "smtp"}


def _redis_env(monkeypatch, **overrides: str) -> None:
    monkeypatch.delenv("REDIS_URL", raising=False)
    for key, value in overrides.items():
        monkeypatch.setenv(key, value)


@pytest.mark.parametrize(
    "backend_var",
    ["CACHE_BACKEND", "EVENT_BUS_BACKEND", "RATE_LIMITER_BACKEND"],
)
def test_redis_backend_without_a_url_fails_at_startup(monkeypatch, backend_var):
    # Fail fast and loudly. Each of these adapters fails *open*, so a missing URL
    # would otherwise boot a healthy-looking process with no cache, no
    # cross-replica events and no rate limit — the exact silent degradation this
    # phase exists to avoid.
    _redis_env(monkeypatch, **{backend_var: "redis"})
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize(
    "backend_var",
    ["CACHE_BACKEND", "EVENT_BUS_BACKEND", "RATE_LIMITER_BACKEND"],
)
def test_redis_backend_with_a_url_is_accepted(monkeypatch, backend_var):
    _redis_env(monkeypatch, REDIS_URL="redis://localhost:6379/0", **{backend_var: "redis"})
    assert Settings(_env_file=None).redis_url == "redis://localhost:6379/0"


def test_backends_default_to_in_process(monkeypatch):
    # A single-worker deploy needs no Redis at all; nothing here is mandatory.
    _redis_env(monkeypatch)
    settings = Settings(_env_file=None)
    assert settings.cache_backend == "memory"
    assert settings.event_bus_backend == "memory"
    assert settings.rate_limiter_backend == "memory"
