"""Cross-cutting request context (framework-free).

Holds the current tenant id in a :class:`~contextvars.ContextVar` so that the
persistence layer can scope every transaction (``SET LOCAL app.tenant_id``) and
repositories can filter by tenant. It is set by the presentation layer (from the
access JWT, or from the tenant resolved during login).

This module imports nothing from the framework layers; domain and application
never touch it — they receive ``tenant_id`` explicitly as a parameter.
"""

from __future__ import annotations

from contextvars import ContextVar, Token

_tenant_ctx: ContextVar[str | None] = ContextVar("app_tenant_id", default=None)


def set_current_tenant(tenant_id: str | None) -> Token:
    """Set the current tenant id; returns a token to restore the previous value."""
    return _tenant_ctx.set(tenant_id)


def get_current_tenant() -> str | None:
    """Return the current tenant id, or ``None`` when no tenant is in context."""
    return _tenant_ctx.get()


def reset_current_tenant(token: Token) -> None:
    """Restore the tenant context to the value captured by ``set_current_tenant``."""
    _tenant_ctx.reset(token)
