from notification.models.boat_charging_models import BoatChargingSession
from notification.models.notification_models import Device


class BoatChargingSessionService:
    def create_boat_charging_session(self, device_id, session_id) -> None:
        device = self._get_device(device_id)
        BoatChargingSession(
            device=device,
            session_id=session_id,
        ).save()

    def _get_device(self, device_id) -> Device:
        device = Device.objects.filter(external_id=device_id)
        if not device.exists():
            device = Device.objects.create(
                external_id=device_id,
                os="unknown",
            )
        return device
