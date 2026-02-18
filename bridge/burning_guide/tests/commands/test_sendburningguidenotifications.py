from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import freezegun
import responses
from django.conf import settings
from django.core.management import call_command
from model_bakery import baker

from bridge.management.commands.sendburningguidenotifications import Command
from bridge.models import BurningGuideNotification
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import ScheduledNotification

tz = ZoneInfo(settings.TIME_ZONE)


class TestCommand(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.command = Command()
        self.zipped_devices = [
            ("device1", "1234"),
            ("device2", "1234"),
            ("device3", "5678"),
        ]
        self.notifications = [
            baker.make(
                BurningGuideNotification, postal_code=postal_code, device_id=device_id
            )
            for device_id, postal_code in self.zipped_devices
        ]

    @freezegun.freeze_time(datetime(2024, 6, 2, 7, 15, 0, tzinfo=tz))
    @patch(
        "bridge.management.commands.sendburningguidenotifications.RIVMService.has_new_red_status"
    )
    def test_command_all_new_red_status(self, patched_has_new_red_status):
        patched_has_new_red_status.return_value = True

        call_command("sendburningguidenotifications")

        self.assertEqual(
            ScheduledNotification.objects.count(), 2
        )  # Two postal codes, so two notifications sent

    @freezegun.freeze_time(datetime(2024, 6, 2, 7, 15, 0, tzinfo=tz))
    @patch(
        "bridge.management.commands.sendburningguidenotifications.RIVMService.has_new_red_status"
    )
    def test_command_no_red_status(self, patched_has_new_red_status):
        patched_has_new_red_status.return_value = False

        call_command("sendburningguidenotifications")

        self.assertEqual(
            ScheduledNotification.objects.count(), 0
        )  # Two postal codes, so two notifications sent

    @freezegun.freeze_time(datetime(2024, 6, 2, 8, 15, 0, tzinfo=tz))
    @patch(
        "bridge.management.commands.sendburningguidenotifications.RIVMService.has_new_red_status"
    )
    def test_command_hour_outside_scope(self, patched_has_new_red_status):
        patched_has_new_red_status.return_value = True

        call_command("sendburningguidenotifications")

        self.assertEqual(
            ScheduledNotification.objects.count(), 0
        )  # Even though there are postal codes, no notifications sent

    @freezegun.freeze_time(datetime(2024, 6, 2, 7, 15, 0, tzinfo=tz))
    @patch(
        "bridge.management.commands.sendburningguidenotifications.RIVMService.has_new_red_status"
    )
    def test_command_complex_case_1(self, patched_has_new_red_status):
        patched_has_new_red_status.side_effect = lambda postal_code: (
            postal_code == "1234"
        )

        call_command("sendburningguidenotifications")

        self.assertEqual(
            ScheduledNotification.objects.count(), 1
        )  # Two devices for postal code 1234
        notification = ScheduledNotification.objects.first()
        device_ids = list(notification.devices.values_list("external_id", flat=True))
        self.assertIn("device1", device_ids)
        self.assertIn("device2", device_ids)

    def test_collect_batched_notifications(self):
        batched = self.command.collect_batched_notifications(self.notifications)
        expected = {
            "1234": ["device1", "device2"],
            "5678": ["device3"],
        }
        self.assertEqual(batched, expected)

    @freezegun.freeze_time(datetime(2024, 6, 2, 23, 0, 0, tzinfo=tz))
    @responses.activate
    def test_send_notification(self):
        notification = self._send_notification()
        self.assertIn("Vanaf 4.00 uur is het Code Rood", notification.body)

    @freezegun.freeze_time(datetime(2024, 6, 2, 16, 15, 0, tzinfo=tz))
    @responses.activate
    def test_send_notification_2(self):
        notification = self._send_notification()
        self.assertIn("Vanaf 22.00 uur is het Code Rood", notification.body)

    def _send_notification(self):
        next_timestamp = self.command._next_fixed_timestamp()
        self.command.send_notification_for_single_postal_code(
            ["device1", "device2"], next_timestamp
        )
        self.assertEqual(ScheduledNotification.objects.count(), 1)
        notification = ScheduledNotification.objects.first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, "Stookwijzer")
        return notification

    @freezegun.freeze_time(datetime(2024, 6, 1, 12, 0, 0, tzinfo=tz))
    def test_last_fixed_timestamp(self):
        last_timestamp = self.command._last_fixed_timestamp()
        expected_timestamp = datetime(
            2024, 6, 1, 10, 0, 0, tzinfo=last_timestamp.tzinfo
        )
        self.assertEqual(last_timestamp, expected_timestamp)

    @freezegun.freeze_time(datetime(2024, 6, 1, 16, 0, 0, tzinfo=tz))
    def test_last_fixed_timestamp_exact_time(self):
        last_timestamp = self.command._last_fixed_timestamp()
        expected_timestamp = datetime(
            2024, 6, 1, 16, 0, 0, tzinfo=last_timestamp.tzinfo
        )
        self.assertEqual(last_timestamp, expected_timestamp)

    @freezegun.freeze_time(datetime(2024, 6, 2, 3, 0, 0, tzinfo=tz))
    def test_last_fixed_timestamp_previous_day(self):
        last_timestamp = self.command._last_fixed_timestamp()
        expected_timestamp = datetime(
            2024, 6, 1, 22, 0, 0, tzinfo=last_timestamp.tzinfo
        )
        self.assertEqual(last_timestamp, expected_timestamp)

    @freezegun.freeze_time(datetime(2024, 6, 1, 12, 0, 0, tzinfo=tz))
    def test_next_fixed_timestamp(self):
        next_timestamp = self.command._next_fixed_timestamp()
        expected_timestamp = datetime(
            2024, 6, 1, 16, 0, 0, tzinfo=next_timestamp.tzinfo
        )
        self.assertEqual(next_timestamp, expected_timestamp)

    @freezegun.freeze_time(datetime(2024, 6, 1, 16, 0, 0, tzinfo=tz))
    def test_next_fixed_timestamp_exact_time(self):
        next_timestamp = self.command._next_fixed_timestamp()
        expected_timestamp = datetime(
            2024, 6, 1, 22, 0, 0, tzinfo=next_timestamp.tzinfo
        )
        self.assertEqual(next_timestamp, expected_timestamp)

    @freezegun.freeze_time(datetime(2024, 6, 2, 23, 0, 0, tzinfo=tz))
    def test_next_fixed_timestamp_next_day(self):
        next_timestamp = self.command._next_fixed_timestamp()
        expected_timestamp = datetime(2024, 6, 3, 4, 0, 0, tzinfo=next_timestamp.tzinfo)
        self.assertEqual(next_timestamp, expected_timestamp)
