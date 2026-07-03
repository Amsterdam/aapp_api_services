from unittest.mock import AsyncMock, patch

import freezegun
from django.conf import settings
from django.core.management import call_command
from model_bakery import baker

from bridge.boat_charging.tests.mock_data import session_detail
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models.boat_charging_models import BoatChargingSession
from notification.models.notification_models import ScheduledNotification


class TestCommand(ResponsesActivatedAPITestCase):
    def setUp(self):
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
    def test_command_completed_session_sends_notification_and_deletes_session(
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
        self.assertEqual(BoatChargingSession.objects.count(), 0)

    @patch(
        "bridge.management.commands.sendboatchargingnotifications.async_fetch",
        new_callable=AsyncMock,
    )
    @freezegun.freeze_time("2026-06-30 06:00:00")
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
    def test_command_mixed_statuses_only_completed_are_notified_and_deleted(
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

        self.assertFalse(
            BoatChargingSession.objects.filter(session_id=self.session_id).exists()
        )
        self.assertTrue(
            BoatChargingSession.objects.filter(session_id="second_session_id").exists()
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
    def test_command_fetch_failure_is_handled(self, mocked_async_fetch):
        mocked_async_fetch.side_effect = Exception("upstream error")

        call_command("sendboatchargingnotifications")

        self.assertEqual(ScheduledNotification.objects.count(), 0)
        self.assertTrue(
            BoatChargingSession.objects.filter(
                session_id=self.session.session_id
            ).exists()
        )
