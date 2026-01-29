from core.enums import Module, NotificationType
from core.services.notification_service import AbstractNotificationService


class NotificationService(AbstractNotificationService):
    module_slug = Module.MIJN_AMS.value
    notification_type = NotificationType.MIJN_AMS_NOTIFICATION.value

    def send(self, notification_data):
        """
        Process the notification data and send notifications.
        """

        self.process(notification_data)
