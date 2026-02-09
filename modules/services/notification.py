import hashlib
import logging
from datetime import datetime

from django.contrib.auth.models import User

from core.services.scheduled_notification import ScheduledNotificationService
from modules.models import Notification, TestDevice

logger = logging.getLogger(__name__)


class NotificationService(ScheduledNotificationService):
    def __init__(self):
        super().__init__()
        self.notification_type = "app:app-notification"
        self.module_slug = "app"

    def send_notification(
        self, notification: Notification, is_test_notification: bool = True
    ):
        device_ids = (
            list(TestDevice.objects.values_list("device_id", flat=True))
            if is_test_notification
            else None
        )
        scheduled_notification = self.upsert(
            title=notification.title,
            body=notification.message,
            scheduled_for=notification.send_at,
            identifier=self._create_identifier(
                created_at=notification.created_at, created_by=notification.created_by
            ),
            context={
                "type": self.notification_type,
                "module_slug": self.module_slug,
                "deeplink": notification.deeplink,
                "url": notification.url,
            },
            notification_type=self.notification_type,
            module_slug=self.module_slug,
            device_ids=device_ids,
            send_all_devices=not is_test_notification,
        )
        notification.nr_sessions = scheduled_notification.devices.count()
        notification.save()

    def _create_identifier(self, created_at: datetime, created_by: User) -> str:
        return f"{self.module_slug}_app_notification_{created_at.strftime('%Y%m%d%H%M%S')}_{hashlib.sha256(created_by.username.encode()).hexdigest()}"
