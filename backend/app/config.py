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

    # CORS — comma-separated allowed origins (the SPA origin in a split-domain
    # deploy). Empty in dev (the Vite proxy makes the SPA same-origin). When set,
    # responses allow credentials so the HttpOnly refresh cookie works cross-site
    # (which also requires COOKIE_SAMESITE=none).
    cors_origins: str = ""

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

    # Payments gateway. "manual" confirms immediately (cash/card/transfer already
    # collected). "mercadopago" creates a Checkout Pro link/QR for online charges
    # (method MERCADOPAGO/QR) and confirms them via webhook. Secrets come from the
    # environment only and are never logged.
    payment_gateway: Literal["manual", "mercadopago"] = "manual"
    mp_access_token: str = ""
    mp_webhook_secret: str = ""
    # Fernet key (url-safe base64, 32 bytes) to encrypt tenants' gateway tokens
    # at rest — Fase 3.5 (MercadoPago OAuth por tenant). Env only.
    credentials_encryption_key: str = ""
    # OAuth app (NÚCLEO's MercadoPago application) for the per-tenant connect flow.
    mp_client_id: str = ""
    mp_client_secret: str = ""
    mp_oauth_redirect_uri: str = ""
    # Optional marketplace fee retained by NÚCLEO per charge, in minor units (0 = off).
    mp_marketplace_fee: int = 0
    # TTL of the signed OAuth ``state`` (anti-CSRF), minutes.
    oauth_state_ttl_min: int = 10

    # Facturación electrónica AFIP. "fake" autoriza al instante (dev/MVP, sin
    # AFIP); "afip" usa WSAA + WSFEv1 reales. AFIP_ENV: homologación vs prod.
    invoicing_provider: str = "fake"
    afip_env: str = "homo"
    # Public URL MercadoPago posts notifications to (a tunnel in dev, the API
    # host in prod). Empty → rely on the dashboard-configured webhook.
    mp_notification_url: str = ""

    # Fichaje por presencia (Fase 5.5). "hmac" = QR/código rotativo firmado;
    # "off" = deshabilitado. El secreto de firma cae al jwt_secret si no se setea.
    presence_provider: Literal["hmac", "off"] = "hmac"
    presence_secret: str = ""
    presence_period_seconds: int = 30
    presence_rate_max: int = 10
    presence_rate_window_seconds: int = 60

    @property
    def effective_presence_secret(self) -> str:
        """Dedicated presence-signing secret, falling back to the JWT secret."""
        return self.presence_secret or self.jwt_secret

    # Asesor financiero (Fase 9). Capa LLM grounded, APAGADA por default: "off" =
    # narración determinística (plantillas); "claude" = Claude narra/sintetiza
    # sobre los números ya calculados (nunca calcula). Prender sólo con evals.
    advisor_llm_provider: Literal["off", "claude"] = "off"
    anthropic_api_key: str = ""
    advisor_llm_model: str = "claude-opus-4-8"

    @property
    def advisor_llm_enabled(self) -> bool:
        return self.advisor_llm_provider != "off"

    # Copiloto IA (Fase 11). "off" (default) = deshabilitado. "claude" = NL→SQL
    # con guardrails (validador + read-only + RLS). La aislación por tenant la da
    # RLS, no el LLM. Prender SÓLO con el set de evals (open question PRD).
    copilot_provider: Literal["off", "claude"] = "off"
    copilot_model: str = "claude-opus-4-8"
    copilot_row_limit: int = 200
    copilot_statement_timeout_ms: int = 5000

    @property
    def copilot_enabled(self) -> bool:
        return self.copilot_provider != "off"

    # Realtime / SSE (Fase 13 T4). KDS y mesas en vivo. El bus es in-process
    # (un worker); para multi-réplica en Railway, swap a un adapter Postgres
    # LISTEN/NOTIFY detrás del port EventBus. El token de stream es un JWT corto
    # porque EventSource no manda header Authorization.
    realtime_token_ttl_s: int = 60
    realtime_heartbeat_s: int = 15

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
        if self.email_transport == "console" and self.env == "production":
            problems.append("EMAIL_TRANSPORT must be 'smtp' (console logs token links)")
        if not self.cookie_secure:
            problems.append("COOKIE_SECURE must be true (refresh cookie over HTTPS only)")
        if self.payment_gateway == "mercadopago":
            if not self.mp_access_token:
                problems.append("MP_ACCESS_TOKEN must be set when PAYMENT_GATEWAY=mercadopago")
            if not self.mp_webhook_secret:
                problems.append("MP_WEBHOOK_SECRET must be set to validate webhooks")
        if problems:
            raise ValueError(f"Insecure settings for env={self.env!r}: " + "; ".join(problems))
        return self
