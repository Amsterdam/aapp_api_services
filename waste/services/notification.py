import logging

from django.utils import timezone

from core.enums import Module, NotificationType
from core.services.notification import AbstractNotificationService, NotificationData
from waste.models import ManualNotification, NotificationSchedule

logger = logging.getLogger(__name__)


class NotificationService(AbstractNotificationService):
    module_slug = Module.WASTE.value
    notification_type = NotificationType.WASTE_DATE_REMINDER.value

    def send(self, device_ids: list[str], waste_type: str):
        notification_data = NotificationData(
            title="Afvalwijzer",
            message=f"Morgen halen we {waste_type.replace('GA', 'grof afval').lower()} in uw buurt op. Ga naar Afvalwijzer.",
            link_source_id=waste_type,
            device_ids=device_ids,
        )
        self.process(notification_data, expiry_minutes=15)


class ManualNotificationService(AbstractNotificationService):
    module_slug = Module.WASTE.value
    notification_type = NotificationType.WASTE_MANUAL_NOTIFICATION.value

    def send(self, notification: ManualNotification):
        device_ids = self.get_device_ids()
        if len(device_ids) > 0:
            notification_data = NotificationData(
                title=notification.title,
                message=notification.message,
                link_source_id=notification.pk,
                device_ids=device_ids,
            )
            self.process(notification_data, expiry_minutes=60)

        notification.send_at = timezone.now()
        notification.nr_sessions = len(device_ids)
        notification.save()

    def get_device_ids(self) -> list[str]:
        return list(NotificationSchedule.objects.values_list("device_id", flat=True))
