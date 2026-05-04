import datetime

from django.utils import timezone

from core.enums import Module, NotificationType
from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)
from core.services.waste_device import WasteDeviceService
from waste.models import ManualNotification

waste_device_service = WasteDeviceService()


class NotificationService(AbstractNotificationService):
    module_slug = Module.WASTE.value
    notification_type = NotificationType.WASTE_DATE_REMINDER.value

    def __init__(self):
        super().__init__()
        self.notification_datetime = datetime.datetime.combine(
            datetime.date.today(), datetime.time(hour=21, minute=0)
        )

    def send(
        self,
        device_ids: list[str],
        waste_type: str,
        notification_datetime: datetime.datetime | None = None,
    ):

        notification = NotificationData(
            title="Afvalwijzer",
            message=f"Morgen halen we {waste_type.lower()} in uw buurt op. Ga naar Afvalwijzer.",
            device_ids=device_ids,
        )

        self.upsert(
            notification=notification,
            scheduled_for=notification_datetime or self.notification_datetime,
            identifier=self._create_identifier(waste_type=waste_type),
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
            self.upsert(notification_data, expiry_minutes=60)

        notification.send_at = timezone.now()
        notification.nr_sessions = len(device_ids)
        notification.save()

    def get_device_ids(self) -> list[str]:
        return waste_device_service.get_device_ids()
