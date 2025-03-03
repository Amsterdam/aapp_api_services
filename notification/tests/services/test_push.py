import logging
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from firebase_admin import messaging

from notification.models import Device, Notification
from notification.services.push import PushService, PushServiceDeviceLimitError
from notification.utils.patch_utils import (
    MockFirebaseSendEach,
    apply_init_firebase_patches,
)


class TestPushService(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.applied_patches = apply_init_firebase_patches()

    @classmethod
    def tearDownClass(cls):
        for p in cls.applied_patches:
            p.stop()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.notification = Notification(
            title="foobar title",
            body="foobar body",
            module_slug="foobar-slug",
            context={"some": "context"},
            created_at="2024-10-31T16:30",
        )
        self.device = Device.objects.create(
            external_id="abc", firebase_token="abc_token"
        )

    def create_devices(self, amount: int, with_token=True, start_id=0):
        new_devices = []
        mock_token = "abc_token" if with_token else None
        for i in range(start_id, start_id + amount):
            device = Device.objects.create(
                external_id=f"abc_{i}", firebase_token=mock_token
            )
            new_devices.append(device)
        return new_devices

    def create_firebase_messages(
        self, created_devices, title="test title", body="test body"
    ):
        messages = []
        for device in created_devices:
            firebase_message = messaging.Message(
                data={},
                notification=messaging.Notification(title=title, body=body),
                token=device.firebase_token,
            )
            messages.append(firebase_message)
        return messages

    @patch("notification.services.push.messaging.send_each")
    def test_push_success(self, multicast_mock):
        messages = self.create_firebase_messages(
            [self.device], title=self.notification.title, body=self.notification.body
        )
        multicast_mock.return_value = MockFirebaseSendEach(messages)

        push_service = PushService(self.notification, [self.device.external_id])
        push_service.push()

        notification = Notification.objects.filter(
            device__external_id=self.device.external_id
        ).first()
        self.assertIsNotNone(notification.pushed_at)

    @patch("notification.services.push.messaging.send_each")
    def test_push_with_some_failed_tokens(self, multicast_mock):
        device_count = 5
        failed_device_count = 2

        created_devices = self.create_devices(device_count)
        messages = self.create_firebase_messages(
            created_devices,
            title=self.notification.title,
            body=self.notification.body,
        )

        multicast_mock.return_value = MockFirebaseSendEach(
            messages, fail_count=failed_device_count
        )

        push_service = PushService(
            self.notification, [c.external_id for c in created_devices]
        )

        logger = logging.getLogger("notification.services.push")
        parent_logger = logger.parent
        parent_logger.setLevel(logging.INFO)
        parent_logger.propagate = True

        with self.assertLogs(logger, level=logging.INFO) as log_context:
            result = push_service.push()

        self.assertTrue(
            any(
                "Failed to send notification to device" in record.message
                for record in log_context.records
            )
        )
        self.assertEqual(Notification.objects.count(), device_count)
        self.assertEqual(result["failed_token_count"], failed_device_count)

    @override_settings(FIREBASE_DEVICE_LIMIT=5)
    def test_hit_max_devices(self):
        device_ids = [f"device_{i}" for i in range(settings.FIREBASE_DEVICE_LIMIT + 1)]

        with self.assertRaises(PushServiceDeviceLimitError):
            PushService(None, device_ids)

    def test_device_without_firebase_tokens(self):
        created_devices = self.create_devices(5, with_token=False)
        device_ids = [c.external_id for c in created_devices]

        push_service = PushService(self.notification, device_ids)

        logger = logging.getLogger("notification.services.push")
        parent_logger = logger.parent
        parent_logger.setLevel(logging.INFO)
        parent_logger.propagate = True

        with self.assertLogs(logger, level=logging.INFO) as log_context:
            result = push_service.push()

        for c in created_devices:
            notification = Notification.objects.filter(
                device__external_id=c.external_id
            ).first()
            self.assertIsNotNone(notification)

        self.assertTrue(
            any(
                "none of the devices have a Firebase token" in record.message
                for record in log_context.records
            )
        )
        self.assertEqual(Notification.objects.count(), len(created_devices))
        self.assertEqual(
            result,
            {
                "devices_with_token_count": 0,
                "failed_token_count": 0,
                "total_device_count": 5,
                "unknown_device_count": 0,
            },
        )

    def test_notifications_created_for_unregistered_device(self):
        device_ids = ["unregistered_device_id"]
        push_service = PushService(self.notification, device_ids)
        push_service.push()

        notification = Notification.objects.filter(
            device__external_id=device_ids[0]
        ).first()
        self.assertIsNotNone(notification)

    @patch("notification.services.push.messaging.send_each")
    def test_notifications_created_for_unknown_devices(self, multicast_mock):
        devices_with_token = self.create_devices(3, with_token=True)

        messages = self.create_firebase_messages(
            devices_with_token,
            title=self.notification.title,
            body=self.notification.body,
        )
        multicast_mock.return_value = MockFirebaseSendEach(messages)

        unknown_device_ids = ["unknown_1", "unknown_2", "unknown_3"]
        all_device_ids = [
            known_device.external_id for known_device in devices_with_token
        ] + unknown_device_ids

        push_service = PushService(self.notification, all_device_ids)
        push_service.push()

        notifications = Notification.objects.filter(
            device__external_id__in=unknown_device_ids
        ).all()
        self.assertEqual(len(notifications), len(unknown_device_ids))

    @patch("notification.services.push.messaging.send_each")
    def test_response_data_counts_for_devices(self, multicast_mock):
        devices_with_token = self.create_devices(3, with_token=True)
        devices_without_token = self.create_devices(
            3, with_token=False, start_id=len(devices_with_token)
        )
        known_devices = devices_with_token + devices_without_token

        messages = self.create_firebase_messages(
            known_devices, title=self.notification.title, body=self.notification.body
        )
        multicast_mock.return_value = MockFirebaseSendEach(messages, fail_count=1)

        unknown_device_ids = ["unknown_1", "unknown_2", "unknown_3"]
        all_device_ids = [
            known_device.external_id for known_device in known_devices
        ] + unknown_device_ids

        push_service = PushService(self.notification, all_device_ids)
        response_data = push_service.push()

        self.assertEqual(
            response_data,
            {
                "devices_with_token_count": len(devices_with_token),
                "failed_token_count": 1,
                "total_device_count": len(all_device_ids),
                "unknown_device_count": len(unknown_device_ids),
            },
        )
