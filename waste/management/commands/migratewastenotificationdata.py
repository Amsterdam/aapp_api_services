import logging
from typing import Any

from django.core.management.base import BaseCommand

from notification.models import WasteDevice
from waste.models import NotificationSchedule

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Migrate waste notification data from waste.NotificationSchedule (default DB)
    to notification.WasteDevice (notification DB).
    """

    help = "Migrate waste notification data from waste.NotificationSchedule (default DB)to notification.WasteDevice (notification DB)."

    def handle(self, *args: Any, **options: Any) -> None:
        old_records = NotificationSchedule.objects.all()

        # Fetch all existing device_ids
        existing_device_ids = set(
            WasteDevice.objects.values_list("device_id", flat=True)
        )

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
                WasteDevice(
                    device_id=record.device_id,
                    bag_nummeraanduiding_id=record.bag_nummeraanduiding_id,
                    created_at=record.created_at,
                    updated_at=record.updated_at,
                )
            )

        if notifications_to_create:
            WasteDevice.objects.bulk_create(notifications_to_create)
            logger.info(f"Created {len(notifications_to_create)} new notifications.")

        # delete old record after migration
        old_records.delete()
        logger.info(f"Skipped {skipped} records (already existed).")
