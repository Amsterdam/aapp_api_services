from core.enums import Module, NotificationType
from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)


class NotificationService(AbstractNotificationService):
    module_slug = Module.BURNING_GUIDE.value
    notification_type = NotificationType.BURNING_GUIDE_NOTIFICATION.value

    def send(self, notification_data: NotificationData):
        """
        Process the notification data and send notifications.
        """

        self.upsert(notification_data)
