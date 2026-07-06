from copy import deepcopy
from datetime import datetime
from unittest.mock import AsyncMock, patch

import freezegun
from django.conf import settings
from django.core.management import call_command
from model_bakery import baker

from bridge.boat_charging.tests.mock_data import session_detail
from bridge.management.commands.sendboatchargingnotifications import Command
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models.boat_charging_models import BoatChargingSession
from notification.models.notification_models import ScheduledNotification


class TestCommand(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.command = Command()
        self.device_id = "device1"
        self.session_id = "ad976dab-73db-4f67-b5f5-77542bf3e088"
        self.session = baker.make(
            BoatChargingSession,
            session_id=self.session_id,
            device__external_id=self.device_id,
        )

    @patch(
        "bridge.management.commands.sendboatchargingnotifications.async_fetch",
        new_callable=AsyncMock,
    )
    def test_command_completed_session_sends_notification_and_marks_session_as_deleted(
        self, mocked_async_fetch
    ):
        mocked_async_fetch.return_value = [session_detail.MOCK_RESPONSE_COMPLETED]

        call_command("sendboatchargingnotifications")

        expected_url = (
            f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{self.session_id}"
        )
        mocked_async_fetch.assert_awaited_once_with(
            [expected_url],
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        )

        self.assertEqual(ScheduledNotification.objects.count(), 1)
        notification = ScheduledNotification.objects.first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, "Laden gestopt")
        self.assertEqual(
            notification.body,
            "Het laden is gestopt. Bekijk uw laadsessie",
        )
        device_ids = list(notification.devices.values_list("external_id", flat=True))
        self.assertEqual(device_ids, [self.device_id])
        self.assertTrue(
            BoatChargingSession.objects.filter(session_id=self.session_id)
            .first()
            .deleted
        )

    @patch(
        "bridge.management.commands.sendboatchargingnotifications.async_fetch",
        new_callable=AsyncMock,
    )
    @freezegun.freeze_time("2026-06-30 02:45:00")
    def test_command_charging_session_first_reminder_sent(self, mocked_async_fetch):

        mocked_async_fetch.return_value = [session_detail.MOCK_RESPONSE_CHARGING]

        call_command("sendboatchargingnotifications")

        self.assertEqual(ScheduledNotification.objects.count(), 1)
        self.assertEqual(ScheduledNotification.objects.first().title, "Herinnering")
        self.assertEqual(BoatChargingSession.objects.count(), 1)
        self.assertIsNotNone(
            BoatChargingSession.objects.filter(session_id=self.session_id)
            .first()
            .first_send_at
        )
        self.assertIsNone(
            BoatChargingSession.objects.filter(session_id=self.session_id)
            .first()
            .second_send_at
        )

    @patch(
        "bridge.management.commands.sendboatchargingnotifications.async_fetch",
        new_callable=AsyncMock,
    )
    @freezegun.freeze_time("2026-06-30 07:00:00")
    def test_command_charging_session_second_reminder_sent(self, mocked_async_fetch):
        self.session.first_send_at = datetime.fromisoformat("2026-06-30T02:00:00+00:00")
        self.session.save(update_fields=["first_send_at"])
        mocked_async_fetch.return_value = [session_detail.MOCK_RESPONSE_CHARGING]

        call_command("sendboatchargingnotifications")

        self.assertEqual(ScheduledNotification.objects.count(), 1)
        notification = ScheduledNotification.objects.first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, "Maximale laadtijd")

        updated_session = BoatChargingSession.objects.get(session_id=self.session_id)
        self.assertIsNotNone(updated_session.first_send_at)
        self.assertIsNotNone(updated_session.second_send_at)
        self.assertIsNone(updated_session.last_send_at)

    @patch(
        "bridge.management.commands.sendboatchargingnotifications.async_fetch",
        new_callable=AsyncMock,
    )
    @freezegun.freeze_time("2026-06-30 12:00:00")
    def test_command_charging_session_hourly_repeat_after_24_hours(
        self, mocked_async_fetch
    ):
        self.session.first_send_at = datetime.fromisoformat("2026-06-30T02:00:00+00:00")
        self.session.second_send_at = datetime.fromisoformat(
            "2026-06-30T06:00:00+00:00"
        )
        self.session.last_send_at = datetime.fromisoformat("2026-06-30T10:00:00+00:00")
        self.session.save(
            update_fields=["first_send_at", "second_send_at", "last_send_at"]
        )
        mocked_async_fetch.return_value = [session_detail.MOCK_RESPONSE_CHARGING]

        call_command("sendboatchargingnotifications")

        self.assertEqual(ScheduledNotification.objects.count(), 1)
        notification = ScheduledNotification.objects.first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, "Kosten na 24 uur")

        updated_session = BoatChargingSession.objects.get(session_id=self.session_id)
        self.assertGreater(updated_session.last_send_at, self.session.last_send_at)

    @patch(
        "bridge.management.commands.sendboatchargingnotifications.async_fetch",
        new_callable=AsyncMock,
    )
    @freezegun.freeze_time("2026-06-30 17:00:00")
    def test_command_charging_session_notifications_send_after_command_failure(
        self, mocked_async_fetch
    ):
        """
        If somehow the command has failed to send notifications for quite some time,
        we dont want to send all notifications at once, but only the last one.
        """

        mocked_async_fetch.return_value = [session_detail.MOCK_RESPONSE_CHARGING]

        call_command("sendboatchargingnotifications")

        self.assertEqual(ScheduledNotification.objects.count(), 1)
        notification = ScheduledNotification.objects.first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, "Kosten na 24 uur")

        updated_session = BoatChargingSession.objects.get(session_id=self.session_id)
        self.assertIsNotNone(updated_session.last_send_at)

    @patch(
        "bridge.management.commands.sendboatchargingnotifications.async_fetch",
        new_callable=AsyncMock,
    )
    @freezegun.freeze_time("2026-06-30 17:00:00")
    def test_command_charging_session_notifications_send_after_restart_command_failure(
        self, mocked_async_fetch
    ):
        """
        This test case is similar to test_command_charging_session_notifications_send_after_command_failure,
        but it simulates a scenario where the command has failed to send notifications for quite some time, and then the command is restarted (like previous test case).

        We want to ensure that no "previous" notifications are sent after the restart. So if last_send_at is set (at 24 hours),
        we should not send notifications that should have been sent at 16 or 20 hours. These will never be sent.
        """
        self.session.last_send_at = datetime.fromisoformat("2026-06-30T16:30:00+00:00")
        self.session.save(update_fields=["last_send_at"])
        mocked_async_fetch.return_value = [session_detail.MOCK_RESPONSE_CHARGING]

        call_command("sendboatchargingnotifications")

        self.assertEqual(ScheduledNotification.objects.count(), 0)

    @patch(
        "bridge.management.commands.sendboatchargingnotifications.async_fetch",
        new_callable=AsyncMock,
    )
    def test_command_charging_session_with_end_datetime_skips_notification(
        self, mocked_async_fetch
    ):
        charging_response = deepcopy(session_detail.MOCK_RESPONSE_CHARGING)
        charging_response["cpmsSession"]["endDateTime"] = "2026-06-30T06:00:00Z"
        mocked_async_fetch.return_value = [charging_response]

        call_command("sendboatchargingnotifications")

        self.assertEqual(ScheduledNotification.objects.count(), 0)
        updated_session = BoatChargingSession.objects.get(session_id=self.session_id)
        self.assertIsNone(updated_session.first_send_at)
        self.assertIsNone(updated_session.second_send_at)
        self.assertIsNone(updated_session.last_send_at)

    @patch(
        "bridge.management.commands.sendboatchargingnotifications.async_fetch",
        new_callable=AsyncMock,
    )
    def test_command_charging_session_without_start_datetime_skips_notification(
        self, mocked_async_fetch
    ):
        charging_response = deepcopy(session_detail.MOCK_RESPONSE_CHARGING)
        charging_response["cpmsSession"].pop("startDateTime")
        mocked_async_fetch.return_value = [charging_response]

        call_command("sendboatchargingnotifications")

        self.assertEqual(ScheduledNotification.objects.count(), 0)
        updated_session = BoatChargingSession.objects.get(session_id=self.session_id)
        self.assertIsNone(updated_session.first_send_at)
        self.assertIsNone(updated_session.second_send_at)
        self.assertIsNone(updated_session.last_send_at)

    @patch(
        "bridge.management.commands.sendboatchargingnotifications.async_fetch",
        new_callable=AsyncMock,
    )
    def test_command_mixed_statuses_only_completed_are_notified_and_marked_as_deleted(
        self, mocked_async_fetch
    ):
        second_device_id = "device2"
        baker.make(
            BoatChargingSession,
            session_id="second_session_id",
            device__external_id=second_device_id,
        )

        mocked_async_fetch.return_value = [
            session_detail.MOCK_RESPONSE_COMPLETED,
            session_detail.MOCK_RESPONSE_CHARGING,
        ]

        call_command("sendboatchargingnotifications")

        self.assertEqual(ScheduledNotification.objects.count(), 1)
        scheduled_notification = ScheduledNotification.objects.first()
        self.assertIsNotNone(scheduled_notification)
        device_ids = list(
            scheduled_notification.devices.values_list("external_id", flat=True)
        )
        self.assertEqual(device_ids, [self.device_id])

        self.assertTrue(
            BoatChargingSession.objects.filter(session_id=self.session_id)
            .first()
            .deleted
        )
        self.assertFalse(
            BoatChargingSession.objects.filter(session_id="second_session_id")
            .first()
            .deleted
        )

    @patch(
        "bridge.management.commands.sendboatchargingnotifications.async_fetch",
        new_callable=AsyncMock,
    )
    def test_command_no_sessions_in_db(self, mocked_async_fetch):
        BoatChargingSession.objects.all().delete()
        mocked_async_fetch.return_value = []

        call_command("sendboatchargingnotifications")

        mocked_async_fetch.assert_awaited_once_with(
            [],
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        )
        self.assertEqual(ScheduledNotification.objects.count(), 0)

    @patch(
        "bridge.management.commands.sendboatchargingnotifications.async_fetch",
        new_callable=AsyncMock,
    )
    def test_command_completed_session_missing_in_db_is_skipped(
        self, mocked_async_fetch
    ):
        BoatChargingSession.objects.filter(session_id=self.session_id).delete()
        mocked_async_fetch.return_value = [session_detail.MOCK_RESPONSE_COMPLETED]

        call_command("sendboatchargingnotifications")

        self.assertEqual(ScheduledNotification.objects.count(), 0)

    def test_build_session_urls(self):
        session_ids = ["session-1", "session-2"]

        session_urls = self.command._build_session_urls(session_ids)

        self.assertEqual(
            session_urls,
            [
                f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/session-1",
                f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/session-2",
            ],
        )

    @patch(
        "bridge.management.commands.sendboatchargingnotifications.async_fetch",
        new_callable=AsyncMock,
    )
    def test_command_fetch_failure_is_handled(self, mocked_async_fetch):
        mocked_async_fetch.side_effect = Exception("upstream error")

        call_command("sendboatchargingnotifications")

        self.assertEqual(ScheduledNotification.objects.count(), 0)
        self.assertTrue(
            BoatChargingSession.objects.filter(
                session_id=self.session.session_id
            ).exists()
        )
