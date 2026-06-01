from core.enums import Module, NotificationType
from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)

LOGOUT_NOTIFICATION_TITLE = "Mijn Amsterdam"
LOGOUT_NOTIFICATION_MESSAGE = (
    "U bent uitgelogd bij Mijn Amsterdam. Log opnieuw in om meldingen te ontvangen."
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


class LogoutNotificationService(AbstractNotificationService):
    module_slug = Module.MIJN_AMS.value
    notification_type = NotificationType.MIJN_AMS_LOGOUT.value

    def send(self, device_ids: list[str]):
        notification_data = NotificationData(
            title=LOGOUT_NOTIFICATION_TITLE,
            message=LOGOUT_NOTIFICATION_MESSAGE,
            device_ids=device_ids,
        )
        self.upsert(notification_data)

    def build_context(self, **kwargs) -> dict:
        kwargs["url"] = "https://mijn.amsterdam.nl/"
        context = super().build_context(**kwargs)
        return context
