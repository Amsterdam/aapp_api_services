import datetime
from datetime import timedelta

from core.enums import Module, NotificationType
from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)
from core.services.waste_device import WasteDeviceService
from waste.models import ManualNotification


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
        device_ids = self.get_device_ids(notification)
        if len(device_ids) > 0:
            notification_data = NotificationData(
                title=notification.title,
                message=notification.message,
                link_source_id=notification.pk,
                device_ids=device_ids,
            )
            scheduled_notification = self.upsert(
                notification=notification_data,
                scheduled_for=notification.send_at,
                expires_at=notification.send_at + timedelta(minutes=30),
                identifier=self._create_identifier(notification.id),
            )
            notification.nr_sessions = scheduled_notification.devices.count()
        else:
            notification.nr_sessions = 0

        notification.save(update_fields=["nr_sessions"])

    def delete_notification(self, notification: ManualNotification):
        identifier = self._create_identifier(notification.id)
        self.delete_scheduled_notification(identifier)

    def _create_identifier(self, notification_id: int) -> str:
        if not notification_id:
            raise ValueError(
                "Notification must be saved and have an id to create an identifier"
            )
        return f"{self.module_slug}_notification_{notification_id}"

    def get_device_ids(self, obj: ManualNotification) -> list[str]:
        waste_device_service = WasteDeviceService()
        route_names = list(obj.affected_routes.values_list("name", flat=True))
        postal_area = obj.affected_postal_area
        bag_ids = waste_device_service.get_device_ids_for_route_names_and_postal_area(
            route_names, postal_area
        )
        return list(set(bag_ids))
