import logging
from unittest.mock import patch

from django.test import TestCase, override_settings
from firebase_admin import messaging
from model_bakery import baker

from notification.crud import NotificationCRUD
from notification.models import (
    Device,
    Notification,
    NotificationPushModuleDisabled,
    NotificationPushTypeDisabled,
)
from notification.utils.patch_utils import apply_init_firebase_patches


class TestNotificationCRUD(TestCase):
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
            notification_type="foobar-type",
            context={},
            created_at="2024-10-31T16:30",
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

    @patch("notification.services.push.messaging.send")
    def test_push_success(self, send_firebase_mock):
        device = baker.make(Device, firebase_token="abc_token")
        send_firebase_mock.return_value = "mock_message_id"

        notification_crud = NotificationCRUD(self.notification)
        notification_crud.create(Device.objects.all())

        notification = Notification.objects.filter(
            device__external_id=device.external_id
        ).first()
        self.assertIsNotNone(notification.pushed_at)
        self.assertEqual(notification.device_external_id, device.external_id)

    @patch("notification.services.push.messaging.send")
    def test_push_notification_ids_are_unique(self, send_firebase_mock):
        devices = self.create_devices(3, with_token=True)
        send_firebase_mock.return_value = "mock_message_id"

        notification_crud = NotificationCRUD(self.notification)
        notification_crud.create(Device.objects.all())

        sent_notification_ids = []
        for call in send_firebase_mock.call_args_list:
            msg = call.args[0]  # The first positional argument to messaging.send
            sent_notification_ids.append(msg.data.get("notificationId"))

        # One push message per device with token
        self.assertEqual(len(sent_notification_ids), len(devices))
        self.assertTrue(all(sent_notification_ids))
        self.assertEqual(len(set(sent_notification_ids)), len(sent_notification_ids))

    @patch("notification.services.push.messaging.send")
    def test_push_missing_token(self, _):
        device = baker.make(Device)
        notification_crud = NotificationCRUD(self.notification)
        notification_crud.create(Device.objects.all())

        notification = Notification.objects.filter(
            device__external_id=device.external_id
        ).first()
        # Check that the notification was created but not pushed
        self.assertIsNone(notification.pushed_at)
        self.assertEqual(notification.device_external_id, device.external_id)

    @patch("notification.services.push.messaging.send")
    def test_push_disabled(self, _):
        device = baker.make(Device, firebase_token="abc_token")
        notification_crud = NotificationCRUD(self.notification, push_enabled=False)
        notification_crud.create(Device.objects.all())

        notification = Notification.objects.filter(
            device__external_id=device.external_id
        ).first()
        # Check that the notification was created but not pushed
        self.assertIsNone(notification.pushed_at)
        self.assertEqual(notification.device_external_id, device.external_id)

    @patch("notification.services.push.messaging.send")
    def test_push_with_some_failed_tokens(self, send_firebase_mock):
        device_count = 5
        self.create_devices(device_count)

        # Simulate failures for the first calls
        send_firebase_mock.side_effect = [
            Exception("Simulated failure"),
            Exception("Simulated failure"),
            "mock_message_id",
            "mock_message_id",
            "mock_message_id",
        ]
        notification_crud = NotificationCRUD(self.notification)

        logger = logging.getLogger("notification.services.push")
        parent_logger = logger.parent
        parent_logger.setLevel(logging.INFO)
        parent_logger.propagate = True
        with self.assertLogs(logger, level=logging.INFO) as log_context:
            notification_crud.create(Device.objects.all())

        self.assertTrue(
            any(
                "Failed to send notification to device" in record.message
                for record in log_context.records
            )
        )
        self.assertEqual(Notification.objects.count(), device_count)
        self.assertEqual(notification_crud.response_data["failed_token_count"], 2)

    @override_settings(FIREBASE_DEVICE_LIMIT=5)
    def test_hit_max_devices(self):
        [baker.make(Device) for i in range(6)]
        device_qs = Device.objects.all()
        NotificationCRUD(self.notification).create(device_qs)

        # Check that the notification was created for all devices
        self.assertEqual(Notification.objects.count(), 6)

    def test_device_without_firebase_tokens(self):
        created_devices = self.create_devices(5, with_token=False)
        device_qs = Device.objects.all()

        notification_crud = NotificationCRUD(self.notification)

        logger = logging.getLogger("notification.crud")
        parent_logger = logger.parent
        parent_logger.setLevel(logging.INFO)
        parent_logger.propagate = True

        with self.assertLogs(logger, level=logging.INFO) as log_context:
            notification_crud.create(device_qs)

        for c in created_devices:
            notification = Notification.objects.filter(
                device__external_id=c.external_id
            ).first()
            self.assertIsNotNone(notification)

        self.assertTrue(
            any(
                "Notification(s) created, but no devices to push to" in record.message
                for record in log_context.records
            )
        )
        self.assertEqual(Notification.objects.count(), len(created_devices))
        self.assertEqual(
            notification_crud.response_data,
            {
                "total_device_count": 5,
                "total_token_count": 0,
                "total_enabled_count": 0,
                "failed_token_count": 0,
            },
        )

    def test_disabled_module(self):
        device = baker.make(Device, firebase_token="abc_token")
        baker.make(NotificationPushModuleDisabled, device=device, module_slug="slug")
        notification = baker.prepare(Notification, module_slug="slug")
        self.assertFalse(Notification.objects.filter(device=device).exists())

        device_qs = Device.objects.all()
        notification_crud = NotificationCRUD(notification)
        notification_crud.create(device_qs)

        self.assertTrue(Notification.objects.filter(device=device).exists())
        self.assertEqual(
            notification_crud.response_data,
            {
                "total_device_count": 1,
                "total_token_count": 1,
                "total_enabled_count": 0,
                "failed_token_count": 0,
            },
        )

    def test_disabled_type(self):
        device = baker.make(Device, firebase_token="abc_token")
        baker.make(
            NotificationPushTypeDisabled, device=device, notification_type="foobar-type"
        )
        notification = baker.prepare(Notification, notification_type="foobar-type")
        self.assertFalse(Notification.objects.filter(device=device).exists())

        device_qs = Device.objects.all()
        notification_crud = NotificationCRUD(notification)
        notification_crud.create(device_qs)

        self.assertTrue(Notification.objects.filter(device=device).exists())
        self.assertEqual(
            notification_crud.response_data,
            {
                "total_device_count": 1,
                "total_token_count": 1,
                "total_enabled_count": 0,
                "failed_token_count": 0,
            },
        )

    @patch("notification.services.push.messaging.send")
    def test_response_data_counts_for_devices(self, send_firebase_mock):
        devices_with_token = self.create_devices(3, with_token=True)
        devices_without_token = self.create_devices(
            3, with_token=False, start_id=len(devices_with_token)
        )
        known_devices = devices_with_token + devices_without_token

        # Simulate one failure for a device with token
        def send_side_effect(msg):
            if msg.token == devices_with_token[0].firebase_token:
                raise Exception("Simulated failure")
            return "mock_message_id"

        send_firebase_mock.side_effect = send_side_effect

        baker.make(
            NotificationPushTypeDisabled,
            device=devices_with_token[0],
            notification_type=self.notification.notification_type,
        )
        baker.make(
            NotificationPushTypeDisabled,
            device=devices_with_token[0],
            notification_type="something other than the notification",
        )
        baker.make(
            NotificationPushTypeDisabled,
            device=devices_with_token[1],
            notification_type="something other than the notification",
        )

        devices_qs = Device.objects.all()
        notification_crud = NotificationCRUD(self.notification)
        notification_crud.create(devices_qs)

        self.assertEqual(
            notification_crud.response_data,
            {
                "total_device_count": len(known_devices),
                "total_token_count": len(devices_with_token),
                "total_enabled_count": len(devices_with_token) - 1,
                "failed_token_count": 2,
            },
        )
