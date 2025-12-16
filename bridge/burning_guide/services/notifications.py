from core.enums import Module, NotificationType
from core.services.notification import AbstractNotificationService


class NotificationService(AbstractNotificationService):
    module_slug = Module.BURNING_GUIDE.value
    notification_type = NotificationType.BURNING_GUIDE_NOTIFICATION.value

    def send(self, notification_data):
        """
        Process the notification data and send notifications.
        """

        self.process(notification_data)
