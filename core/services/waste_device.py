from datetime import date, datetime, time

from django.db.models import Q
from django.utils import timezone

from notification.models import WasteDevice


class WasteDeviceService:
    def get_device_ids(self) -> list[str]:
        return list(WasteDevice.objects.values_list("device_id", flat=True))

    def bulk_create_waste_devices(self, waste_devices: list[WasteDevice]):
        WasteDevice.objects.bulk_create(waste_devices)

    def define_waste_device_instance(
        self, device_id: str, bag_nummeraanduiding_id: str, updated_at: datetime
    ) -> WasteDevice:
        return WasteDevice(
            device_id=device_id,
            bag_nummeraanduiding_id=bag_nummeraanduiding_id,
            updated_at=updated_at,
        )

    def get_outdated_waste_devices(self) -> list[WasteDevice]:
        return list(
            WasteDevice.objects.filter(
                Q(updated_at__lt=datetime.combine(date.today(), time.min))
                | Q(updated_at__isnull=True)
            )
        )

    def update_waste_device(self, ids_to_update: list[str]):
        WasteDevice.objects.filter(pk__in=ids_to_update).update(
            updated_at=timezone.now()
        )
