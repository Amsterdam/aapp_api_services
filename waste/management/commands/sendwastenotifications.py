import datetime
import logging
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from waste.models import NotificationSchedule
from waste.services.notification import call_notification_service
from waste.services.waste_collection import WasteCollectionService

logger = logging.getLogger(__name__)
DAYS_AHEAD = 1


class Command(BaseCommand):
    help = "Send notifications for waste"

    def handle(self, *args, **options):
        notification_date = datetime.datetime.today() + datetime.timedelta(
            days=DAYS_AHEAD
        )
        logger.info(
            "Sending notifications",
            extra={"notification_date": notification_date},
        )

        # get the datetime of today with the time set to 00:00
        today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        notification_schedules = list(
            NotificationSchedule.objects.filter(
                Q(updated_at__lt=today) | Q(updated_at__isnull=True)
            )
        )
        batched_notifications = self.collect_batched_notifications(
            notification_date, notification_schedules
        )
        self.send_notifications(batched_notifications)

        # Mark all schedules as updated, to prevent sending the same notification multiple times
        ids_to_update = [schedule.pk for schedule in notification_schedules]
        NotificationSchedule.objects.filter(pk__in=ids_to_update).update(
            updated_at=timezone.now()
        )

    def collect_batched_notifications(
        self,
        notification_date: datetime,
        notification_schedules: list[NotificationSchedule],
    ):
        batched_notifications = defaultdict(list)
        for schedule in notification_schedules:
            try:
                waste_service = WasteCollectionService(schedule.bag_nummeraanduiding_id)
                waste_service.get_validated_data()
                calendar = waste_service.create_calendar()
                next_dates = waste_service.get_next_dates(calendar)
            except Exception:
                logger.error(
                    "Failed to get waste schedule",
                    extra={
                        "bag_nummeraanduiding_id": schedule.bag_nummeraanduiding_id,
                        "device_id": schedule.device_id,
                    },
                )
                continue

            for waste_type, date in next_dates.items():
                if date == notification_date.date():
                    batched_notifications[waste_type].append(schedule.device_id)
        return batched_notifications

    def send_notifications(self, batched_notifications):
        for type, device_ids in batched_notifications.items():
            # Send in batches of 500 devices
            for i in range(0, len(device_ids), 500):
                batch = device_ids[i : i + 500]
                call_notification_service(batch, type)
                logger.info(
                    "Sent notification", extra={"type": type, "device_ids": batch}
                )
