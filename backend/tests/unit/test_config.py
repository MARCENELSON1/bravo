from __future__ import annotations

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
