from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from bridge.parking.enums import NotificationStatus
from bridge.parking.services.reminder_scheduler import ParkingReminderScheduler


class TestReminderScheduler(TestCase):
    @patch(
        "bridge.parking.services.reminder_scheduler.ScheduledNotificationService.upsert"
    )
    def test_create_new_reminder_for_unknown_identifier(self, mock_upsert_reminder):
        reminder_key = "test-reminder-key"
        scheduler = ParkingReminderScheduler(
            reminder_key=reminder_key,
            end_datetime=timezone.now()
            + timedelta(minutes=settings.PARKING_REMINDER_TIME + 1),
            device_id="foobar",
        )
        notification_status = scheduler.process()
        self.assertEqual(notification_status, NotificationStatus.CREATED)
        self.assertEqual(mock_upsert_reminder.call_count, 1)

    @patch(
        "bridge.parking.services.reminder_scheduler.ScheduledNotificationService.delete"
    )
    def test_dont_create_reminder_since_end_datetime_is_too_soon(
        self, mock_delete_reminder
    ):
        reminder_key = "test-reminder-key"
        scheduler = ParkingReminderScheduler(
            reminder_key=reminder_key,
            end_datetime=timezone.now()
            + timedelta(minutes=settings.PARKING_REMINDER_TIME - 1),
            device_id="foobar",
        )
        notification_status = scheduler.process()
        self.assertEqual(notification_status, NotificationStatus.CANCELLED)
        self.assertEqual(mock_delete_reminder.call_count, 1)

    @patch(
        "bridge.parking.services.reminder_scheduler.ScheduledNotificationService.upsert"
    )
    def test_update_existing_reminder(self, mock_upsert_reminder):
        reminder_key = "test-reminder-key"
        scheduler = ParkingReminderScheduler(
            reminder_key=reminder_key,
            end_datetime=timezone.now()
            + timedelta(minutes=settings.PARKING_REMINDER_TIME + 1),
            device_id="foobar2",
        )
        notification_status = scheduler.process()
        self.assertEqual(notification_status, NotificationStatus.CREATED)
        self.assertEqual(mock_upsert_reminder.call_count, 1)

    @patch(
        "bridge.parking.services.reminder_scheduler.ScheduledNotificationService.delete"
    )
    def test_delete_reminder_if_end_datetime_is_in_the_past(self, mock_delete_reminder):
        reminder_key = "test-reminder-key"
        scheduler = ParkingReminderScheduler(
            reminder_key=reminder_key,
            end_datetime=timezone.now() - timedelta(minutes=1),
            device_id="foobar",
        )
        notification_status = scheduler.process()
        self.assertEqual(notification_status, NotificationStatus.CANCELLED)
        self.assertEqual(mock_delete_reminder.call_count, 1)
