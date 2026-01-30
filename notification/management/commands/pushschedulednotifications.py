import logging
from time import sleep

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from notification.crud import NotificationCRUD
from notification.models import Notification, ScheduledNotification

logger = logging.getLogger(__name__)
BATCH_SIZE = 1  # Don't batch and let the multiple worker pods handle parallelism


class Command(BaseCommand):
    help = "Push scheduled notifications"

    def add_arguments(self, parser):
        parser.add_argument("--test-mode", action="store_true")

    def handle(self, *args, **options):
        while True:
            with transaction.atomic():
                # Select all scheduled notifications that have not been pushed yet.
                # select_for_update() is used to lock the database rows one by one to prevent duplicate pushes.
                # If another parallel process is running, it will skip the locked rows and move on to the next ones.
                timezone_now = timezone.now()
                notifications_to_process = (
                    ScheduledNotification.objects.select_for_update(
                        skip_locked=True
                    ).filter(scheduled_for__lte=timezone_now)[:BATCH_SIZE]
                )
                notifications_to_process = list(notifications_to_process)
                if not notifications_to_process:
                    logger.debug("No scheduled notifications found. Sleeping...")
                    if options["test_mode"]:
                        # In test mode, interrupt the loop when no notifications are found
                        break
                    sleep(5)  # Sleep for 5 seconds before checking again
                if options["test_mode"]:
                    for n in notifications_to_process:
                        n.make_push = False
                logger.info(
                    f"Pushing {len(notifications_to_process)} scheduled notifications"
                )
                self.process_notifications(notifications_to_process)

    def process_notifications(
        self, notifications_to_process: list[ScheduledNotification]
    ):
        for scheduled_notification in notifications_to_process:
            if scheduled_notification.expires_at <= timezone.now():
                logger.info(
                    "Skipping expired notification",
                    extra={
                        "notification_type": scheduled_notification.notification_type,
                        "created_at": scheduled_notification.created_at,
                        "scheduled_for": scheduled_notification.scheduled_for,
                    },
                )
            else:
                try:
                    self.process(scheduled_notification)
                except Exception as e:
                    logger.error(
                        "Error processing scheduled notification",
                        exc_info=e,
                        extra={
                            "notification_type": scheduled_notification.notification_type,
                            "context": scheduled_notification.context,
                        },
                    )
            scheduled_notification.delete()

    def process(self, scheduled_notification: ScheduledNotification):
        notification_obj = Notification(
            title=scheduled_notification.title,
            body=scheduled_notification.body,
            module_slug=scheduled_notification.module_slug,
            context=scheduled_notification.context,
            notification_type=scheduled_notification.notification_type,
            image=scheduled_notification.image,
            created_at=timezone.now(),
        )
        scheduled_notification.devices.all()
        notification_crud = NotificationCRUD(
            source_notification=notification_obj,
            push_enabled=scheduled_notification.make_push,
        )
        response = notification_crud.create(
            device_qs=scheduled_notification.devices.all()
        )
        logger.debug(response)
