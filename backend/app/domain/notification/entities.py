from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class DeviceToken:
    """A push token for one of a user's devices (Fase 4). Scoped by tenant + user;
    ``token`` is the FCM registration token, unique across devices."""

    id: str
    tenant_id: str
    user_id: str
    token: str
    platform: str  # "ios" | "android"
    created_at: datetime | None = None
