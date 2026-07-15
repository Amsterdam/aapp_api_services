import logging

from django.db.models import QuerySet

from notification.models.notification_models import Device

logger = logging.getLogger(__name__)


def create_missing_device_ids(device_ids: list[str]) -> QuerySet:
    existing_external_ids = set(
        Device.objects.filter(external_id__in=device_ids).values_list(
            "external_id", flat=True
        )
    )
    missing_device_ids = set(device_ids) - existing_external_ids
    if missing_device_ids:
        Device.objects.bulk_create(
            (Device(external_id=device_id) for device_id in missing_device_ids),
            ignore_conflicts=True,
        )
        logger.info("Created %s missing devices.", len(missing_device_ids))
    return Device.objects.filter(external_id__in=device_ids).values_list(
        "id", flat=True
    )
