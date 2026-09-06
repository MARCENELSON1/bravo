"""Push that does not make the kitchen wait.

Sending a push means loading the user's device tokens, minting a Google OAuth
token and POSTing to FCM once per device — hundreds of milliseconds of network
that used to sit inside the request that marks a course ready. The KDS gains
nothing by waiting for it: the mozo's phone is not going to hear about the plate
any faster because the tap was slow.

So this decorator implements the same port and only writes a row. The real
service runs later, from the drainer. Everything the notification says is already
rendered by the time it lands here, so what goes out is a snapshot of the moment
the plate was ready — not of whatever the comanda looks like when it is sent.
"""

from __future__ import annotations

import logging

from app.application.outbox.ports import OutboxKind, OutboxPort
from app.domain.notification.ports import NotificationService, PushMessage

logger = logging.getLogger(__name__)


class OutboxPushService(NotificationService):
    def __init__(self, outbox: OutboxPort) -> None:
        self._outbox = outbox

    async def notify_user(
        self, *, tenant_id: str, user_id: str, message: PushMessage
    ) -> None:
        try:
            await self._outbox.enqueue(
                tenant_id,
                OutboxKind.PUSH_NOTIFICATION,
                {
                    "user_id": user_id,
                    "title": message.title,
                    "body": message.body,
                    "data": dict(message.data),
                },
            )
        except Exception:  # noqa: BLE001
            # An aviso is secondary to the operation that triggered it: failing to
            # queue it must never break marking a plate ready.
            logger.warning(
                "push enqueue failed for user %s", user_id, exc_info=True
            )
