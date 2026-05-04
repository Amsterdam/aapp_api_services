from core.enums import Module, NotificationType
from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)


class NotificationService(AbstractNotificationService):
    module_slug = Module.MIJN_AMS.value
    notification_type = NotificationType.MIJN_AMS_NOTIFICATION.value

    def send(self, notification_data: NotificationData):
        """
        Process the notification data and send notifications.
        """

        self.upsert(notification_data)

    def build_context(self, **kwargs) -> dict:
        kwargs["url"] = "https://mijn.amsterdam.nl/"
        context = super().build_context(**kwargs)
        return context
