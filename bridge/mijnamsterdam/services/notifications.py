from core.enums import Module
from core.services.notification import AbstractNotificationService


class NotificationService(AbstractNotificationService):
    module_slug = Module.MIJN_AMS.value

    def send(self, notification_data):
        """
        Process the notification data and send notifications.
        """

        self.process(notification_data)
