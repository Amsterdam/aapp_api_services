from datetime import datetime

from core.enums import Module, NotificationType
from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)


class NotificationService(AbstractNotificationService):
    module_slug = Module.PARKING.value
    notification_type = NotificationType.PARKING_REMINDER.value

    def send(
        self,
        notification_data: NotificationData,
        identifier: str,
        scheduled_for: datetime,
        expires_at: datetime,
        context: dict[str, str],
    ):
        """
        Process the notification data and send notifications.
        """

        self.upsert(
            notification=notification_data,
            identifier=identifier,
            scheduled_for=scheduled_for,
            expires_at=expires_at,
            context=context,
        )
