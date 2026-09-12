from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PushMessage:
    """A push notification's content + deep-link ``data`` (order_id/kind). The
    title/body are user-facing → Spanish (UX). ``data`` values are all strings
    (both APNs and FCM carry a string→string payload)."""

    title: str
    body: str
    data: dict[str, str] = field(default_factory=dict)


class NotificationService(ABC):
    """Sends a push to a user's registered devices (Fase 4). Lives behind a flag:
    ``NullPushService`` (default, no-op) or ``FcmPushService`` (real FCM). Called
    from the use cases at the same point they publish the SSE event, so the aviso
    reaches the mozo even with the app closed."""

    @abstractmethod
    async def notify_user(
        self, *, tenant_id: str, user_id: str, message: PushMessage
    ) -> None: ...
