import logging

from core.enums import Module, NotificationType
from core.services.notification import AbstractNotificationService, NotificationData

logger = logging.getLogger(__name__)


class NotificationService(AbstractNotificationService):
    module_slug = Module.WASTE.value
    notification_type = NotificationType.WASTE_DATE_REMINDER.value

    def send(self, device_ids: list[str], type: str):
        notification_data = NotificationData(
            title=f"Morgen wordt je {type} afval opgehaald",
            message="Denk er aan om je container buiten te zetten",
            link_source_id=type,
            device_ids=device_ids,
        )
        self.process(notification_data)
