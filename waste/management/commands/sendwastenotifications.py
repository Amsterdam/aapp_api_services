import logging
from collections import defaultdict

from django.core.management.base import BaseCommand

from core.services.waste_device import WasteDeviceService
from waste.constants import WASTE_COLLECTION_ROUTE_TYPES
from waste.services.notification import NotificationService
from waste.services.waste_collection_notification import (
    WasteCollectionNotificationService,
)
from waste.models import WasteCollectionRouteName

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Send notifications for Waste"""

    help = "Send notifications for waste"

    def __init__(self):
        super().__init__()
        self.waste_device_service = WasteDeviceService()
        self.notification_service = NotificationService()
        self.collection_service = WasteCollectionNotificationService()
        self.notification_schedules = (
            self.waste_device_service.get_outdated_waste_devices()
        )
        logger.info(
            "Initialized command.",
            extra=dict(
                total_registered_devices=len(self.notification_schedules),
            ),
        )

    def handle(self, *args, **options):
        """
        This function is called when the management command is executed.
        It loads all waste collection records for different waste types,
        filters them based on whether the pickup day is tomorrow, collects device IDs
        for notifications, and schedules the notifications accordingly.
        """
        # Check if tomorrow is an exception date before processing
        if len(self.collection_service.all_dates) == 0:
            logger.warning(
                "Tomorrow is an exception on waste collection. No notifications will be sent."
            )
            return

        full_data = []
        route_names = set()
        for route_type_code in WASTE_COLLECTION_ROUTE_TYPES:
            logger.info(
                "Fetching data for route", extra={"route_type_code": route_type_code}
            )
            waste_data, waste_route_names = self.collection_service.get_validated_data_for_route_type_code(
                route_type=route_type_code
            )
            full_data.extend(waste_data)
            route_names.update(waste_route_names)

        logger.info("Fetched all waste data from Waste Guide API.")
        logger.info("Sending notifications")
        devices_per_fraction = self._get_devices_per_fraction(filtered_data=full_data)
        self._send_notifications(fraction_device_ids=devices_per_fraction)

        logger.info("Updating waste device records with last notification timestamp")
        ids_to_update = [schedule.pk for schedule in self.notification_schedules]
        self.waste_device_service.update_waste_device(ids_to_update=ids_to_update)

        logger.info("Updating waste route names")
        WasteCollectionRouteName.objects.bulk_create(
            [WasteCollectionRouteName(name=route_name) for route_name in route_names],
            ignore_conflicts=True,
        )


    def _get_devices_per_fraction(
        self, filtered_data: list[dict]
    ) -> dict[str, list[str]]:
        devices_per_fraction = defaultdict(list)
        device_ids_per_bag_id = self._get_device_ids_per_bag_id()
        for data in filtered_data:
            bag_nummeraanduiding_id = data.get("bag_id", "") or ""
            # get waste type from data
            fraction = data.get("label")
            if not fraction:
                logger.warning(
                    "No waste type found. Skipping notification.",
                    extra={"bag_nummeraanduiding_id": bag_nummeraanduiding_id},
                )
                continue
            device_ids = device_ids_per_bag_id[bag_nummeraanduiding_id]
            devices_per_fraction[fraction] += device_ids
        return devices_per_fraction

    def _get_device_ids_per_bag_id(self):
        """Filter notification schedules to only those that need to be sent"""
        device_ids_per_bag_id = defaultdict(list)
        for schedule in self.notification_schedules:
            device_ids_per_bag_id[schedule.bag_nummeraanduiding_id].append(
                schedule.device_id
            )
        return device_ids_per_bag_id

    def _send_notifications(self, fraction_device_ids: dict[str, list[str]]):
        """send notifications to all device ids"""
        for waste_type, device_ids in fraction_device_ids.items():
            deduplicated_device_ids = list(set(device_ids))
            if deduplicated_device_ids:
                self.notification_service.send(
                    device_ids=deduplicated_device_ids,
                    waste_type=waste_type,
                )
                logger.info(
                    f"Scheduled notifications for {waste_type} - {len(deduplicated_device_ids)} devices",
                    extra={
                        "type": waste_type,
                        "nr_devices": len(deduplicated_device_ids),
                    },
                )
