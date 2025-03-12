import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from notification.models import Notification, ScheduledNotification
from notification.services.push import PushService

logger = logging.getLogger(__name__)
BATCH_SIZE = 100


class Command(BaseCommand):
    help = "Push scheduled notifications"

    def handle(self, *args, **options):
        while True:
            with transaction.atomic():
                # Select all scheduled notifications that have not been pushed yet.
                # select_for_update() is used to lock the database rows one by one to prevent duplicate pushes.
                # If another parallel process is running, it will skip the locked rows and move on to the next ones.
                notifications_to_push = ScheduledNotification.objects.select_for_update(
                    skip_locked=True
                ).filter(pushed_at__isnull=True, scheduled_for__lte=timezone.now())[
                    :BATCH_SIZE
                ]
                notifications_to_push = list(notifications_to_push)
                if not notifications_to_push:
                    logger.info("Finished pushing scheduled notifications")
                    break
                logger.info(
                    f"Pushing {len(notifications_to_push)} scheduled notifications"
                )
                self.push_notifications(notifications_to_push)

    def push_notifications(self, notifications_to_push):
        for scheduled_notification in notifications_to_push:
            self.push_notification(scheduled_notification)

    def push_notification(self, scheduled_notification):
        notification_obj = Notification(
            title=scheduled_notification.title,
            body=scheduled_notification.body,
            module_slug=scheduled_notification.module_slug,
            context=scheduled_notification.context,
            notification_type=scheduled_notification.notification_type,
            image=scheduled_notification.image,
            created_at=timezone.now(),
            schedule=scheduled_notification,
        )
        scheduled_notification.devices.all()
        response = PushService(
            source_notification=notification_obj,
            devices_qs=scheduled_notification.devices.all(),
        ).push()
        logger.debug(response)

        # Update the pushed_at flag to prevent duplicate pushes!!!
        scheduled_notification.pushed_at = timezone.now()
        scheduled_notification.save()
