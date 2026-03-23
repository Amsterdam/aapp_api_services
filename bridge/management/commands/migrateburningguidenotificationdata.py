import logging
from typing import Any

from django.core.management.base import BaseCommand

from bridge.models import BurningGuideNotification
from core.services.burning_guide_device import BurningGuideDeviceService

logger = logging.getLogger(__name__)

burning_guide_device_service = BurningGuideDeviceService()


class Command(BaseCommand):
    """
    Migrate burning guide notification data from bridge.BurningGuideNotification (default DB)
    to notification.BurningGuideDevice (notification DB).
    """

    help = "Migrate burning guide notification data from bridge.BurningGuideNotification (default DB)to notification.BurningGuideDevice (notification DB)."

    def handle(self, *args: Any, **options: Any) -> None:
        old_records = BurningGuideNotification.objects.all()

        # Fetch all existing device_ids
        existing_device_ids = set(burning_guide_device_service.get_device_ids())

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
                burning_guide_device_service.define_burning_guide_device_instance(
                    device_id=record.device_id,
                    postal_code=record.postal_code,
                    send_at=record.send_at,
                )
            )

        if notifications_to_create:
            burning_guide_device_service.bulk_create_burning_guide_devices(
                notifications_to_create
            )
            logger.info(f"Created {len(notifications_to_create)} new notifications.")

        # delete old record after migration
        old_records.delete()
        logger.info(f"Skipped {skipped} records (already existed).")
