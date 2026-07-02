import asyncio
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from bridge.boat_charging.services.notifications import NotificationService
from core.services.boat_charging_sessions import BoatChargingSessionService
from core.services.notification_service import NotificationData
from core.utils.async_utils import _async_fetch

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Send notifications from Boat Charging."""

    help = "Send notifications from Boat Charging."

    def __init__(self):
        super().__init__()
        self.notification_service = NotificationService()
        self.boat_charging_session_service = BoatChargingSessionService()

    def handle(self, *args, **options):
        session_ids = (
            self.boat_charging_session_service.get_all_boat_charging_session_ids()
        )
        session_urls = self._build_session_urls(session_ids)
        sessions_data = self._fetch_sessions_data(session_urls)

        for session_data in sessions_data:
            self._process_session_data_for_completed_notifications(session_data)

    def _build_session_urls(self, session_ids: list[str]) -> list[str]:
        base_url = settings.BOAT_CHARGING_ENDPOINTS["SESSIONS"]
        return [f"{base_url}/{session_id}" for session_id in session_ids]

    def _fetch_sessions_data(self, session_urls: list[str]) -> list[dict]:
        try:
            fetched = asyncio.run(_async_fetch(session_urls))
        except Exception:
            logger.exception("Boat charging session fetch failed.")
            return []

        return fetched

    def _process_session_data_for_completed_notifications(self, session_data: dict):
        session = session_data.get("session", {})
        session_id = session.get("uniqueId")
        status = session.get("status")

        # Only process completed sessions (status 4)
        # TODO: once other statuses are supported, this will need to be updated
        if status != 4:
            return

        boat_charging_session = (
            self.boat_charging_session_service.get_boat_charging_session_by_session_id(
                session_id
            )
        )

        if boat_charging_session is None:
            logger.warning(
                "Completed session not found in database; skipping notification.",
                extra={
                    "session_id": session_id,
                },
            )
            return

        device_id = boat_charging_session.device.external_id
        try:
            notification_data = NotificationData(
                title="Laden gestopt",
                message="Het laden is gestopt. Bekijk uw laadsessie",
                device_ids=[device_id],
            )
            self.notification_service.send(notification_data)

            self.boat_charging_session_service.delete_boat_charging_session(
                device_id=device_id,
                session_id=session_id,
            )
        except Exception:
            logger.error(
                "Failed processing completed boat charging session.",
                extra={
                    "session_id": session_id,
                },
            )
