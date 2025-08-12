from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from bridge.parking.enums import NotificationStatus
from bridge.parking.services.reminder_scheduler import ParkingReminderScheduler


class TestReminderScheduler(TestCase):
    @patch(
        "bridge.parking.services.reminder_scheduler.ScheduledNotificationService.get"
    )
    @patch(
        "bridge.parking.services.reminder_scheduler.ScheduledNotificationService.add"
    )
    def test_create_new_reminder_for_unknown_identifier(
        self, mock_add_reminder, mock_get_reminder
    ):
        mock_get_reminder.return_value = None

        reminder_key = "test-reminder-key"
        scheduler = ParkingReminderScheduler(
            reminder_key=reminder_key,
            end_datetime=timezone.now()
            + timedelta(minutes=settings.PARKING_REMINDER_TIME + 1),
            device_id="foobar",
            report_code="foobar",
        )
        notification_status = scheduler.process()
        self.assertEqual(notification_status, NotificationStatus.CREATED)
        self.assertEqual(mock_add_reminder.call_count, 1)

    @patch(
        "bridge.parking.services.reminder_scheduler.ScheduledNotificationService.get"
    )
    @patch(
        "bridge.parking.services.reminder_scheduler.ScheduledNotificationService.add"
    )
    def test_dont_create_reminder_since_end_datetime_is_too_soon(
        self, mock_add_reminder, mock_get_reminder
    ):
        mock_get_reminder.return_value = None

        reminder_key = "test-reminder-key"
        scheduler = ParkingReminderScheduler(
            reminder_key=reminder_key,
            end_datetime=timezone.now()
            + timedelta(minutes=settings.PARKING_REMINDER_TIME - 1),
            device_id="foobar",
            report_code="foobar",
        )
        notification_status = scheduler.process()
        self.assertEqual(notification_status, NotificationStatus.NO_CHANGE)
        self.assertEqual(mock_add_reminder.call_count, 0)

    @patch(
        "bridge.parking.services.reminder_scheduler.ScheduledNotificationService.get"
    )
    @patch(
        "bridge.parking.services.reminder_scheduler.ScheduledNotificationService.update"
    )
    def test_update_existing_reminder(self, mock_update_reminder, mock_get_reminder):
        mock_get_reminder.return_value = {"device_ids": ["foobar1"], "pushed_at": None}

        reminder_key = "test-reminder-key"
        scheduler = ParkingReminderScheduler(
            reminder_key=reminder_key,
            end_datetime=timezone.now()
            + timedelta(minutes=settings.PARKING_REMINDER_TIME + 1),
            device_id="foobar2",
            report_code="foobar",
        )
        notification_status = scheduler.process()
        self.assertEqual(notification_status, NotificationStatus.UPDATED)
        self.assertEqual(mock_update_reminder.call_count, 1)

    @patch(
        "bridge.parking.services.reminder_scheduler.ScheduledNotificationService.get"
    )
    @patch(
        "bridge.parking.services.reminder_scheduler.ScheduledNotificationService.delete"
    )
    def test_delete_reminder_if_end_datetime_is_in_the_past(
        self, mock_delete_reminder, mock_get_reminder
    ):
        mock_get_reminder.return_value = {"pushed_at": None}

        reminder_key = "test-reminder-key"
        scheduler = ParkingReminderScheduler(
            reminder_key=reminder_key,
            end_datetime=timezone.now() - timedelta(minutes=1),
            device_id="foobar",
            report_code="foobar",
        )
        notification_status = scheduler.process()
        self.assertEqual(notification_status, NotificationStatus.CANCELLED)
        self.assertEqual(mock_delete_reminder.call_count, 1)
