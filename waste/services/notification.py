import datetime
import logging

from django.conf import settings
from django.utils import timezone

from core.enums import Module, NotificationType
from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)
from core.services.waste_device import WasteDeviceService
from waste.models import ManualNotification
from waste.services.waste_collection_abstract import WasteCollectionAbstractService

waste_device_service = WasteDeviceService()

logger = logging.getLogger(__name__)


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
            self.upsert(notification_data, expiry_minutes=60)

        notification.send_at = timezone.now()
        notification.nr_sessions = len(device_ids)
        notification.save()

    def get_device_ids(self, obj: ManualNotification) -> list[str]:
        if obj.affected_routes.exists():
            print("There are affected routes, getting bag ids for those routes")
            all_bag_ids = set()
            for route in obj.affected_routes.all():
                bag_ids = self.get_bag_ids_for_route_name(route.name)
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
            logger.info(f"Fetching data for route {route_name}")
            waste_data_batch, next_link = self.get_validated_data(
                url=next_link, params=params
            )
            logger.info(
                f"Fetched {len(waste_data_batch)} bag ids for route {route_name}"
            )
            bag_ids.update(
                item.get("bag_nummeraanduiding_id") for item in waste_data_batch
            )
            params = None  # params are included in the next_link url already
        return list(bag_ids)
