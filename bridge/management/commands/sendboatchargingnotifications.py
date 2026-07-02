import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from bridge.boat_charging.services.notifications import NotificationService
from core.services.boat_charging_sessions import BoatChargingSessionService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Send notifications from Boat Charging."""

    help = "Send notifications from Boat Charging."

    def __init__(self):
        super().__init__()
        self.notification_service = NotificationService()
        self.boat_charging_session_service = BoatChargingSessionService()

    def handle(self, *args, **options):
        now = timezone.now()

        devices = self.boat_charging_session_service.get_all_boat_charging_sessions()

        for device in devices:
            print(now, device)

        # for device in devices:
        #     if not device.session_id:
        #         continue

        #     # Check if session is still active
        #     # TODO: Handle inactieve sessions (e.g., if the session has ended, we maybe want to send a notification and delete record from database)

        #     duration_hours = (now - device.created_at).total_seconds() // 3600

        #     updated = False  # track if we need to save

        #     # Handle base thresholds
        #     for n_notification, threshold_str in self.notification_thresholds.items():
        #         hours = int(threshold_str[:-1])

        #         if duration_hours >= hours and n_notification:
        #             notification_data = NotificationData(
        #                 link_source_id="",
        #                 title="Boot laden herinnering",
        #                 message=".",
        #                 device_ids=[device.device_id],
        #             )
        #             self.notification_service.send(notification_data)

        #             sent[key] = now.isoformat()
        #             updated = True

        #     # Handle repeating notifications after last threshold
        #     last_threshold = base_thresholds[-1]

        #     if duration >= last_threshold:
        #         extra_time = duration - last_threshold
        #         repeat_count = int(extra_time // repeat_delta)

        #         for i in range(1, repeat_count + 1):
        #             total_duration = last_threshold + i * repeat_delta
        #             hours = int(total_duration.total_seconds() // 3600)
        #             key = str(hours)

        #             if key not in sent:
        #                 notification_data = NotificationData(
        #                     link_source_id="",
        #                     title="Haal je boot van de laadpaal",
        #                     message="Je betaald nu een kleeftarief voor het laden van je boot. Haal je boot van de laadpaal.",
        #                     device_ids=[device.device_id],
        #                 )
        #                 self.notification_service.send(notification_data)

        #                 sent[key] = now.isoformat()
        #                 updated = True

        #     # 4. Save only if something changed
        #     if updated:
        #         device.sent_notifications = sent
        #         device.save(update_fields=["sent_notifications"])
