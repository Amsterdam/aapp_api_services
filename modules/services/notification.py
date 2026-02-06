import logging
import uuid

from core.services.scheduled_notification import ScheduledNotificationService
from modules.models import Notification

logger = logging.getLogger(__name__)


class NotificationService(ScheduledNotificationService):
    def __init__(self):
        super().__init__()
        self.notification_type = "app:app-notification"
        self.module_slug = "app"

    def send_notification(self, notification: Notification):
        scheduled_notification = self.upsert(
            title=notification.title,
            body=notification.message,
            scheduled_for=notification.send_at,
            identifier=self._create_identifier(),
            context={
                "type": self.notification_type,
                "module_slug": self.module_slug,
            },
            notification_type=self.notification_type,
            module_slug=self.module_slug,
        )
        notification.nr_sessions = scheduled_notification.devices.count()
        notification.save()

    def _create_identifier(self) -> str:
        return f"{self.module_slug}_app_notification_{uuid.uuid4()}"
