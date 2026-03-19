
import logging
from typing import Any

from django.core.management.base import BaseCommand

from waste.models import NotificationSchedule
from notification.models import WasteNotification

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Migrate waste notification data from the old notification service to the new one."""

    help = "Migrate waste notification data from the old notification service to the new one."

    def handle(self, *args: Any, **options: Any) -> None:
        old_records = NotificationSchedule.objects.all()

        # Fetch all existing (device_id, bag_nummeraanduiding_id) pairs
        existing_pairs = set(
            WasteNotification.objects.values_list("device_id", "bag_nummeraanduiding_id")
        )

        notifications_to_create = []
        skipped = 0

        for record in old_records:
            pair = (record.device_id, record.bag_nummeraanduiding_id)
            if pair in existing_pairs:
                logger.info(
                    f"Notification already exists for device {record.device_id} and bag_nummeraanduiding_id {record.bag_nummeraanduiding_id}, skipping migration for record {record.pk}"
                )
                skipped += 1
                continue
            notifications_to_create.append(
                WasteNotification(
                    device_id=record.device_id,
                    bag_nummeraanduiding_id=record.bag_nummeraanduiding_id,
                    created_at=record.created_at,
                    updated_at=record.updated_at
                )
            )

        if notifications_to_create:
            WasteNotification.objects.bulk_create(notifications_to_create)
            logger.info(f"Created {len(notifications_to_create)} new notifications.")
        logger.info(f"Skipped {skipped} records (already existed).")