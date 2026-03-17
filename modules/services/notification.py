import logging
from datetime import timedelta

from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)
from modules.models import Notification, TestDevice

logger = logging.getLogger(__name__)


class NotificationService(AbstractNotificationService):
    module_slug = "modules"
    notification_type = "modules:general-notification"

    def send(self, notification: Notification, is_test_notification: bool = True):
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

        notification_data = NotificationData(
            title=notification.title,
            message=notification.message,
            link_source_id=str(notification.pk),
            device_ids=device_ids,
        )
        scheduled_notification = self.upsert(
            notification=notification_data,
            scheduled_for=notification.send_at,
            expires_at=notification.send_at + timedelta(minutes=30),
            identifier=self._create_identifier(notification.id),
            context=context,
            send_all_devices=not is_test_notification,
        )
        notification.nr_sessions = scheduled_notification.devices.count()
        notification.save()

    def delete_general_notification(self, notification: Notification):
        identifier = self._create_identifier(notification.id)
        self.delete_scheduled_notification(identifier)

    def _create_identifier(self, notification_id: int) -> str:
        assert notification_id, "Notification must have an id to create an identifier"
        return f"{self.module_slug}_app_notification_{notification_id}"
