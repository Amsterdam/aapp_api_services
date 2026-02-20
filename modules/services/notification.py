import hashlib
import logging
from datetime import datetime

from django.contrib.auth.models import User

from core.services.scheduled_notification import ScheduledNotificationService
from modules.models import Notification, TestDevice

logger = logging.getLogger(__name__)


class NotificationService:
    module_slug = "modules"
    notification_type = "modules:general-notification"

    def __init__(self):
        self.notification_service = ScheduledNotificationService()

    def send_notification(
        self, notification: Notification, is_test_notification: bool = True
    ):
        device_ids = (
            list(TestDevice.objects.values_list("device_id", flat=True))
            if is_test_notification
            else None
        )
        context = {
            "type": self.notification_type,
            "module_slug": self.module_slug,
        }
        if notification.deeplink:
            context["deeplink"] = notification.deeplink
        if notification.url:
            context["url"] = notification.url
        scheduled_notification = self.notification_service.upsert(
            title=notification.title,
            body=notification.message,
            scheduled_for=notification.send_at,
            identifier=self._create_identifier(
                created_at=notification.created_at, created_by=notification.created_by
            ),
            context=context,
            notification_type=self.notification_type,
            module_slug=self.module_slug,
            device_ids=device_ids,
            send_all_devices=not is_test_notification,
        )
        notification.nr_sessions = scheduled_notification.devices.count()
        notification.save()

    def delete_scheduled_notification(self, notification: Notification):
        identifier = self._create_identifier(
            created_at=notification.created_at, created_by=notification.created_by
        )
        self.notification_service.delete(identifier)

    def _create_identifier(self, created_at: datetime, created_by: User) -> str:
        return f"{self.module_slug}_app_notification_{created_at.strftime('%Y%m%d%H%M%S')}_{hashlib.sha256(created_by.username.encode()).hexdigest()}"
