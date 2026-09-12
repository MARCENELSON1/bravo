from __future__ import annotations

import logging

from app.domain.notification.ports import NotificationService, PushMessage

logger = logging.getLogger(__name__)


class NullPushService(NotificationService):
    """No-op push (default, ``PUSH_PROVIDER=none``): logs and returns. Lets the whole
    feature ship + run without any FCM setup — the SSE aviso still works in-app."""

    async def notify_user(
        self, *, tenant_id: str, user_id: str, message: PushMessage
    ) -> None:
        logger.debug(
            "push (noop) tenant=%s user=%s title=%s", tenant_id, user_id, message.title
        )
