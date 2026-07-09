import logging

from django.db.models import QuerySet

from notification.models.notification_models import Device

logger = logging.getLogger(__name__)


def create_missing_device_ids(device_ids: list[str]) -> QuerySet[Device]:
    existing_devices = Device.objects.filter(external_id__in=device_ids).values_list(
        "external_id", flat=True
    )
    missing_device_ids = set(device_ids) - set(existing_devices)
    if missing_device_ids:
        Device.objects.bulk_create(
            Device(external_id=device_id) for device_id in missing_device_ids
        )
        logger.info(f"Created {len(missing_device_ids)} missing devices.")
    return Device.objects.filter(external_id__in=device_ids).values_list(
        "id", flat=True
    )
