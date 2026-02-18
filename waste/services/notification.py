import datetime
import logging

from django.utils import timezone

from core.enums import Module, NotificationType
from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)
from core.services.scheduled_notification import ScheduledNotificationService
from waste.models import ManualNotification, NotificationSchedule

logger = logging.getLogger(__name__)


class NotificationService(ScheduledNotificationService):
    def __init__(self):
        super().__init__()
        self.notification_datetime = datetime.datetime.combine(
            datetime.date.today(), datetime.time(hour=21, minute=0)
        )

    def send_waste_notification(
        self,
        device_ids: list[str],
        waste_type: str,
        notification_datetime: datetime.datetime | None = None,
    ):
        self.upsert(
            title="Afvalwijzer",
            body=f"Morgen halen we {waste_type.lower()} in uw buurt op. Ga naar Afvalwijzer.",
            scheduled_for=notification_datetime or self.notification_datetime,
            identifier=self._create_identifier(waste_type=waste_type),
            context={
                "type": NotificationType.WASTE_DATE_REMINDER.value,
                "module_slug": Module.WASTE.value,
            },
            device_ids=device_ids,
            notification_type=NotificationType.WASTE_DATE_REMINDER.value,
            module_slug=Module.WASTE.value,
        )

    def _create_identifier(self, waste_type: str) -> str:
        return f"{Module.WASTE.value}_{waste_type.replace(' ', '-')}_reminder"


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
