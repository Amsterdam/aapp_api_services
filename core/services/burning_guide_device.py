from datetime import datetime

from django.db.models import Q
from django.utils import timezone

from notification.models import BurningGuideDevice


class BurningGuideDeviceService:
    def get_device_ids(self) -> list[str]:
        return list(BurningGuideDevice.objects.values_list("device_id", flat=True))

    def bulk_create_burning_guide_devices(
        self, burning_guide_devices: list[BurningGuideDevice]
    ) -> None:
        BurningGuideDevice.objects.bulk_create(burning_guide_devices)

    def define_burning_guide_device_instance(
        self, device_id: str, postal_code: str, send_at: datetime
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
                Q(send_at__lt=last_timestamp) | Q(send_at__isnull=True)
            )
        )

    def update_burning_guide_devices(self, device_ids: list[str]) -> None:
        BurningGuideDevice.objects.filter(pk__in=device_ids).update(
            send_at=timezone.now()
        )
