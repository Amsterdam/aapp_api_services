import asyncio
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from bridge.boat_charging.services.notifications import NotificationService
from core.services.boat_charging_sessions import BoatChargingSessionService
from core.services.notification_service import NotificationData
from core.utils.async_utils import async_fetch

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Send notifications from Boat Charging."""

    help = "Send notifications from Boat Charging."

    def __init__(self):
        super().__init__()
        self.notification_service = NotificationService()
        self.boat_charging_session_service = BoatChargingSessionService()
        self.notification_settings = [
            {
                "column_name": "first_send_at",
                "hours": 16,
                "title": "Herinnering",
                "message": "Uw boot is nog aan het laden.",
            },
            {
                "column_name": "second_send_at",
                "hours": 20,
                "title": "Maximale laadtijd",
                "message": "Uw boot mag maximaal 24 uur laden. Daarna betaalt u €2,00 per uur. Ook als u maar een deel van een uur gebruikt, betaalt u voor het hele uur",
            },
            {
                "column_name": "last_send_at",
                "hours": 24,
                "title": "Kosten na 24 uur",
                "message": "Uw boot ligt langer dan 24 uur bij het laadpunt. U betaalt nu €2,00 per uur. Ook als u maar een deel van een uur gebruikt, betaalt u voor het hele uur",
            },
        ]

    def handle(self, *args, **options):
        session_ids = (
            self.boat_charging_session_service.get_all_boat_charging_session_ids()
        )
        session_urls = self._build_session_urls(session_ids)
        sessions_data = self._fetch_sessions_data(session_urls)

        for session_data in sessions_data:
            if not session_data:
                continue

            session = session_data.get("session", {})
            session_id = session.get("uniqueId")
            status = session.get("status")
            cpms_session = session_data.get("cpmsSession", {})

            if status == 3:  # Charging session
                self._process_session_data_for_charging_notifications(
                    session_id, cpms_session
                )

            elif (
                status == 4
            ):  # Completed session (change this later if the status codes change)
                self._process_session_data_for_completed_notifications(session_id)

    def _build_session_urls(self, session_ids: list[str]) -> list[str]:
        base_url = settings.BOAT_CHARGING_ENDPOINTS["SESSIONS"]
        return [f"{base_url}/{session_id}" for session_id in session_ids]

    def _fetch_sessions_data(self, session_urls: list[str]) -> list[dict]:
        try:
            fetched = asyncio.run(
                async_fetch(
                    session_urls,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0",  # necessary to get through WAF
                    },
                )
            )
        except Exception:
            logger.exception("Boat charging session fetch failed.")
            return []

        return fetched

    def _process_session_data_for_completed_notifications(self, session_id: str):
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
            logger.exception(
                "Failed processing completed boat charging session.",
                extra={
                    "session_id": session_id,
                },
            )

    def _process_session_data_for_charging_notifications(
        self, session_id: str, cpms_session: dict
    ):
        boat_charging_session = (
            self.boat_charging_session_service.get_boat_charging_session_by_session_id(
                session_id
            )
        )

        if boat_charging_session is None:
            logger.warning(
                "Charging session not found in database; skipping notification.",
                extra={
                    "session_id": session_id,
                },
            )
            return

        if cpms_session.get("endDateTime"):
            return

        start_time_str = cpms_session.get("startDateTime")
        if not start_time_str:
            return

        start_time = timezone.datetime.fromisoformat(
            start_time_str.replace("Z", "+00:00")
        )
        hours_since_start = (timezone.now() - start_time).total_seconds() // 3600

        notification_to_send = self._determine_notification_to_send(
            hours_since_start=hours_since_start,
            boat_charging_session=boat_charging_session,
        )

        if notification_to_send:
            device_id = boat_charging_session.device.external_id
            try:
                notification_data = NotificationData(
                    title=notification_to_send["title"],
                    message=notification_to_send["message"],
                    device_ids=[device_id],
                )
                self.notification_service.send(notification_data)

                self.boat_charging_session_service.update_boat_charging_session(
                    device_id=device_id,
                    session_id=session_id,
                    update_dict={notification_to_send["column_name"]: timezone.now()},
                )
            except Exception:
                logger.exception(
                    "Failed processing charging boat charging session.",
                    extra={
                        "session_id": session_id,
                        "notification_setting": notification_to_send,
                    },
                )

        # after 24 hours, we send a new notification every hour, so we need to update the last_send_at column to the current time
        if hours_since_start >= 24:
            last_send_at = boat_charging_session.last_send_at
            if last_send_at is None:
                hours_since_last_send = 1
            else:
                hours_since_last_send = (
                    timezone.now() - boat_charging_session.last_send_at
                ).total_seconds() // 3600
            if hours_since_last_send >= 1:
                device_id = boat_charging_session.device.external_id
                try:
                    notification_data = NotificationData(
                        title=self.notification_settings[-1]["title"],
                        message=self.notification_settings[-1]["message"],
                        device_ids=[device_id],
                    )
                    self.notification_service.send(notification_data)

                    self.boat_charging_session_service.update_boat_charging_session(
                        device_id=device_id,
                        session_id=session_id,
                        update_dict={"last_send_at": timezone.now()},
                    )
                except Exception:
                    logger.exception(
                        "Failed processing charging boat charging session.",
                        extra={
                            "session_id": session_id,
                        },
                    )

    def _determine_notification_to_send(
        self, hours_since_start: int, boat_charging_session
    ) -> dict | None:
        """
        Function to determine which notification to send based on the hours since the charging session started and the notification settings.

        """
        due_notification_settings = [
            notification_setting
            for notification_setting in self.notification_settings
            if hours_since_start == notification_setting["hours"]
            and not getattr(boat_charging_session, notification_setting["column_name"])
        ]

        if len(due_notification_settings) == 0:
            return None
        else:
            return due_notification_settings[
                0
            ]  # Return the first due notification setting
