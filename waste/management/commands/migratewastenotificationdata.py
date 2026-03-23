import logging
from typing import Any

from django.core.management.base import BaseCommand

from core.services.waste_device import WasteDeviceService
from waste.models import NotificationSchedule

logger = logging.getLogger(__name__)

waste_device_service = WasteDeviceService()


class Command(BaseCommand):
    """
    Migrate waste notification data from waste.NotificationSchedule (default DB)
    to notification.WasteDevice (notification DB).
    """

    help = "Migrate waste notification data from waste.NotificationSchedule (default DB)to notification.WasteDevice (notification DB)."

    def handle(self, *args: Any, **options: Any) -> None:
        old_records = NotificationSchedule.objects.all()

        # Fetch all existing device_ids
        existing_device_ids = set(waste_device_service.get_device_ids())

        notifications_to_create = []
        skipped = 0

        for record in old_records:
            if record.device_id in existing_device_ids:
                logger.info(
                    f"Record already exists, skipping migration for record {record.pk}"
                )
                skipped += 1
                continue
            notifications_to_create.append(
                waste_device_service.define_waste_device_instance(
                    device_id=record.device_id,
                    bag_nummeraanduiding_id=record.bag_nummeraanduiding_id,
                    updated_at=record.updated_at,
                )
            )

        if notifications_to_create:
            waste_device_service.bulk_create_waste_devices(notifications_to_create)
            logger.info(f"Created {len(notifications_to_create)} new notifications.")

        # delete old record after migration
        old_records.delete()
        logger.info(f"Skipped {skipped} records (already existed).")
