from django.utils import timezone

from notification.models import BoatChargingDevice, Device


class BoatChargingDeviceService:
    def get_device_ids(self) -> list[str]:
        return list(BoatChargingDevice.objects.values_list("device_id", flat=True))

    def bulk_create_boat_charging_devices(
        self, boat_charging_devices: list[BoatChargingDevice]
    ) -> None:
        BoatChargingDevice.objects.bulk_create(boat_charging_devices)

    def create_boat_charging_device(
        self, device_id: str, session_id: str
    ) -> BoatChargingDevice:
        return BoatChargingDevice.objects.create(
            device_id=device_id,
            session_id=session_id,
        )

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

    def define_boat_charging_device_instance(
        self, device_id: str, session_id: str
    ) -> BoatChargingDevice:
        return BoatChargingDevice(
            device_id=device_id,
            session_id=session_id,
        )

    def get_all_boat_charging_devices(
        self,
    ) -> list[BoatChargingDevice]:
        return list(BoatChargingDevice.objects.all())

    def update_boat_charging_devices(self, device_ids: list[str]) -> None:
        BoatChargingDevice.objects.filter(pk__in=device_ids).update(
            send_at=timezone.now()
        )
