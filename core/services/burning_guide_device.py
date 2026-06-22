from datetime import datetime

from django.db.models import Q
from django.utils import timezone

from notification.models import BurningGuideDevice, Device


class BurningGuideDeviceService:
    def get_device_ids(self) -> list[str]:
        return list(BurningGuideDevice.objects.values_list("device_id", flat=True))

    def bulk_create_burning_guide_devices(
        self, burning_guide_devices: list[BurningGuideDevice]
    ) -> None:
        BurningGuideDevice.objects.bulk_create(burning_guide_devices)

    def ensure_devices_exist(self, device_ids: list[str]) -> None:
        existing_external_ids = set(
            Device.objects.filter(external_id__in=device_ids).values_list(
                "external_id", flat=True
            )
        )
        missing_external_ids = set(device_ids) - existing_external_ids
        if missing_external_ids:
            Device.objects.bulk_create(
                [
                    Device(external_id=external_id, os="unknown")
                    for external_id in missing_external_ids
                ],
                ignore_conflicts=True,
            )

    def define_burning_guide_device_instance(
        self, device_id: str, postal_code: str, send_at: datetime | None
    ) -> BurningGuideDevice:
        return BurningGuideDevice(
            device_id=device_id,
            postal_code=postal_code,
            send_at=send_at,
        )

    def get_outdated_burning_guide_devices(
        self, last_timestamp: datetime
    ) -> list[BurningGuideDevice]:
        return list(
            BurningGuideDevice.objects.filter(
                (Q(send_at__lt=last_timestamp) | Q(send_at__isnull=True))
                & Q(postal_code__isnull=False)
            )
        )

    def update_burning_guide_devices(self, device_ids: list[str]) -> None:
        BurningGuideDevice.objects.filter(pk__in=device_ids).update(
            send_at=timezone.now()
        )
