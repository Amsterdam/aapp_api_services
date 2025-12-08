import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from bridge.parking.config import DEFAULT_LANGUAGE, REMINDER_MESSAGES
from bridge.parking.enums import NotificationStatus
from core.enums import Module, NotificationType
from core.services.scheduled_notification import ScheduledNotificationService

logger = logging.getLogger(__name__)


class ReminderSchedulerError(Exception):
    pass


class ParkingReminderScheduler:
    def __init__(
        self,
        reminder_key: str,
        end_datetime: datetime,
        device_id: str,
        report_code: str | None,
    ):
        self.schedule_service = ScheduledNotificationService()

        self.device_id = device_id
        self.report_code = report_code
        self.reminder_key = reminder_key
        self.identifier = self._create_identifier(reminder_key)

        self.log_extra = {
            "reminder_key": reminder_key,
            "end_datetime": end_datetime,
        }
        self.end_datetime = end_datetime
        self.reminder_time = self._get_reminder_time(end_datetime)
        self.log_extra["reminder_time"] = self.reminder_time

    def process(self) -> NotificationStatus:
        if self.reminder_time:
            self.schedule_reminder()
            logger.info("Creating reminder", extra=self.log_extra)
            return NotificationStatus.CREATED
        else:
            logger.info("Deleting reminder", extra=self.log_extra)
            self.schedule_service.delete(self.identifier)
            return NotificationStatus.CANCELLED

    def schedule_reminder(
        self,
        locale: str = DEFAULT_LANGUAGE,
    ):
        content = REMINDER_MESSAGES.get(locale)
        context = {
            "reminderKey": self.reminder_key,
            "type": NotificationType.PARKING_REMINDER.value,
            "module_slug": Module.PARKING.value,
        }
        if self.report_code:
            context["reportCode"] = str(self.report_code)
        self.schedule_service.upsert(
            title=content.title,
            body=content.body,
            identifier=self.identifier,
            scheduled_for=self.reminder_time,
            expires_at=self.end_datetime,
            context=context,
            device_ids=[self.device_id],
            notification_type=NotificationType.PARKING_REMINDER.value,
            module_slug=Module.PARKING.value,
        )

    def _get_reminder_time(self, end_datetime: datetime) -> datetime | None:
        reminder_time = end_datetime - timedelta(minutes=settings.PARKING_REMINDER_TIME)
        if reminder_time <= timezone.now():
            # Don't schedule reminder if the time is in the past
            # Also, this deletes the reminder if it exists
            logger.info(
                "End time is too close to current time",
                extra=self.log_extra,
            )
            return None
        return reminder_time

    def _create_identifier(self, reminder_key: str) -> str:
        return f"{Module.PARKING.value}_parking-reminder_{reminder_key}"
