import logging
from collections import defaultdict
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from bridge.burning_guide.services.notifications import NotificationService
from bridge.burning_guide.services.rivm import RIVMService
from bridge.models import BurningGuideNotification
from core.services.notification import NotificationData

logger = logging.getLogger(__name__)
rivm_client = RIVMService()


class Command(BaseCommand):
    """Send notifications from Burning Guide."""

    help = "Send notifications from Burning Guide."

    def __init__(self):
        super().__init__()
        self.notification_service = NotificationService()

    def handle(self, *args, **kwargs):
        last_timestamp = self._last_fixed_timestamp()
        notification_devices = list(
            BurningGuideNotification.objects.filter(
                Q(send_at__lt=last_timestamp) | Q(send_at__isnull=True)
            )
        )
        batched_notifications = self.collect_batched_notifications(notification_devices)
        for postal_code, device_ids in batched_notifications.items():
            try:
                if rivm_client.has_new_red_status(postal_code):
                    logger.info(
                        "Sending notifications for postal code",
                        extra={"postal_code": postal_code},
                    )
                    next_timestamp = self._next_fixed_timestamp()
                    self.send_notification_for_single_postal_code(
                        device_ids, next_timestamp
                    )
                else:
                    logger.info(
                        "No new red status for postal code, skipping notification",
                        extra={"postal_code": postal_code},
                    )

                # Mark devices within postal code as updated, to prevent sending the same notification multiple times
                BurningGuideNotification.objects.filter(pk__in=device_ids).update(
                    send_at=timezone.now()
                )
            except Exception as e:
                logger.error(
                    f"Error sending notifications: {e}",
                    exc_info=True,
                    extra={
                        "postal_code": postal_code,
                    },
                )

    def collect_batched_notifications(
        self,
        notification_devices: list[BurningGuideNotification],
    ):
        """We batch notifications per postal code, so we send one notification to multiple devices"""
        batched_notifications = defaultdict(list)
        for device in notification_devices:
            batched_notifications[device.postal_code].append(device.device_id)
        return batched_notifications

    def send_notification_for_single_postal_code(self, device_ids, next_timestamp):
        notification_data = NotificationData(
            link_source_id="burning_guide",
            title="Stookwijzer",
            message=f"Vanaf {next_timestamp.hour}.00 uur is het Code Rood: Stook geen hout. Ga naar Stookwijzer.",
            device_ids=device_ids,
        )
        self.notification_service.send(notification_data)

    def _last_fixed_timestamp(self):
        now = timezone.now()
        hours = [22, 16, 10, 4]
        # Find the most recent hour <= now.hour
        for h in hours:
            if now.hour >= h:
                return now.replace(hour=h, minute=0, second=0, microsecond=0)

        # If none matched (now < 04:00), fallback to yesterday 22:00
        return (now - timedelta(days=1)).replace(
            hour=22, minute=0, second=0, microsecond=0
        )

    def _next_fixed_timestamp(self):
        now = datetime.now()
        hours = [4, 10, 16, 22]
        # Find the next hour > now.hour
        for h in hours:
            if now.hour < h:
                return now.replace(hour=h, minute=0, second=0, microsecond=0)

        # If none matched (now >= 22:00), fallback to tomorrow 04:00
        return (now + timedelta(days=1)).replace(
            hour=4, minute=0, second=0, microsecond=0
        )
