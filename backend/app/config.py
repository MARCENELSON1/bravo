"""Application settings (pydantic-settings).

Loaded from environment variables / ``.env``. Secrets are never logged.
All identifiers are in English per the project language convention.
"""

from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_JWT_SECRET = "change-me-in-production"
_DEFAULT_DATABASE_URL = "postgresql+asyncpg://bravo_app:bravo_app@localhost:5432/bravo_dev"


class Settings(BaseSettings):
    """Typed configuration for the BRAVO backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "dev"

    # Database — the app connects with a dedicated NON-superuser role so that
    # Postgres Row Level Security (RLS) is actually enforced (FORCE RLS).
    database_url: str = _DEFAULT_DATABASE_URL

    # JWT
    jwt_secret: str = _DEFAULT_JWT_SECRET
    jwt_alg: Literal["HS256", "HS384", "HS512"] = "HS256"
    access_token_ttl_min: int = 15
    refresh_token_ttl_days: int = 30

    # One-time tokens (stored hashed, single-use, with a short TTL)
    reset_token_ttl_min: int = 30
    verification_token_ttl_hours: int = 24
    invitation_token_ttl_hours: int = 72

    # Email — UX content is in Spanish. Transport "console" prints the link to
    # stdout (dev, no SMTP server needed); "smtp" sends through aiosmtplib.
    email_transport: str = "console"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str | None = None
    smtp_password: str | None = None
    from_email: str = "no-reply@bravo.app"
    smtp_use_tls: bool = True

    # Base URL used to build links inside emails (points to the frontend).
    app_base_url: str = "http://localhost:5173"

    # Refresh-token cookie. The refresh token is delivered as an HttpOnly cookie
    # scoped to the auth endpoints (the SPA never reads it); the access token
    # stays in the JSON body and is kept in memory. See README "Token storage".
    refresh_cookie_name: str = "bravo_refresh"
    cookie_secure: bool = True
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_path: str = "/api/v1/auth"

    # Login throttling / lockout
    max_login_attempts: int = 5
    lockout_minutes: int = 15

    @model_validator(mode="after")
    def _reject_insecure_production(self) -> "Settings":
        """Fail fast on insecure configuration outside of dev."""
        if self.env == "dev":
            return self
        problems: list[str] = []
        if self.jwt_secret == _DEFAULT_JWT_SECRET:
            problems.append("JWT_SECRET must be a strong random value")
        if self.database_url == _DEFAULT_DATABASE_URL:
            problems.append("DATABASE_URL must be set explicitly")
        if not self.app_base_url.startswith("https://"):
            problems.append("APP_BASE_URL must use https")
        if self.email_transport == "console":
            problems.append("EMAIL_TRANSPORT must be 'smtp' (console logs token links)")
        if not self.cookie_secure:
            problems.append("COOKIE_SECURE must be true (refresh cookie over HTTPS only)")
        if problems:
            raise ValueError(f"Insecure settings for env={self.env!r}: " + "; ".join(problems))
        return self
