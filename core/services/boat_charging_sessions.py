import logging

from notification.models.boat_charging_models import BoatChargingSession
from notification.models.notification_models import Device

logger = logging.getLogger(__name__)


class BoatChargingSessionService:
    def create_boat_charging_session(self, device_id, session_id) -> None:
        device = self._get_device(device_id)
        BoatChargingSession(
            device=device,
            session_id=session_id,
        ).save()

    def _get_device(self, device_id) -> Device:
        device = Device.objects.filter(external_id=device_id).first()
        if device is None:
            device = Device.objects.create(
                external_id=device_id,
                os="unknown",
            )
        return device

    def update_boat_charging_session(
        self, device_id: str, session_id: str, update_dict: dict
    ) -> None:
        try:
            BoatChargingSession.objects.filter(
                device__external_id=device_id,
                session_id=session_id,
                deleted=False,
            ).update(
                **update_dict
            )  # Update the specified column of the existing session
        except Exception:
            logger.exception(
                "Failed to update boat charging session.",
                extra={
                    "device_id": device_id,
                    "session_id": session_id,
                    "update_dict": update_dict,
                },
            )

    def mark_boat_charging_session_as_deleted(self, device_id, session_id):
        try:
            BoatChargingSession.objects.filter(
                device__external_id=device_id,
                session_id=session_id,
            ).update(deleted=True)  # Mark the session as deleted
        except Exception:
            logger.exception(
                "Failed to mark boat charging session as deleted.",
                extra={
                    "device_id": device_id,
                    "session_id": session_id,
                },
            )

    def get_boat_charging_session_by_session_id(
        self, session_id: str
    ) -> BoatChargingSession | None:
        try:
            return BoatChargingSession.objects.get(session_id=session_id, deleted=False)
        except BoatChargingSession.DoesNotExist:
            return None

    def get_all_boat_charging_session_ids(self) -> list[str]:
        return list(
            BoatChargingSession.objects.filter(deleted=False).values_list(
                "session_id", flat=True
            )
        )
