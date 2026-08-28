import datetime
from datetime import timedelta

from django.conf import settings

from core.enums import Module, NotificationType
from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)
from core.services.waste_device import WasteDeviceService
from waste.models import ManualNotification
from waste.services.waste_collection_abstract import WasteCollectionAbstractService

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


class ManualNotificationService(
    AbstractNotificationService, WasteCollectionAbstractService
):
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
        route_names = list(obj.affected_routes.values_list("name", flat=True))
        if route_names:
            all_bag_ids = set()
            for route_name in route_names:
                bag_ids = self.get_bag_ids_for_route_name(route_name)
                all_bag_ids.update(bag_ids)
            return waste_device_service.get_device_ids_for_bag_ids(list(all_bag_ids))
        return waste_device_service.get_device_ids()

    def get_bag_ids_for_route_name(self, route_name: str) -> list[str]:
        """Get all bag_nummeraanduiding_id's for a given route_name from the waste guide API."""

        params = {
            "afvalwijzerRoutenaam": route_name,
            "_pageSize": 20000,
        }
        next_link = settings.WASTE_GUIDE_URL

        bag_ids = set()
        while next_link:
            waste_data_batch, next_link = self.get_validated_data(
                url=next_link, params=params
            )
            bag_ids.update(
                item["bag_nummeraanduiding_id"]
                for item in waste_data_batch
                if item.get("bag_nummeraanduiding_id")
            )
            params = None  # params are included in the next_link url already
        return list(bag_ids)
