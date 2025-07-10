from unittest.mock import patch

from django.test import TestCase, override_settings
from model_bakery import baker

from notification.models import Device, Notification
from notification.services.push import PushService
from notification.utils.patch_utils import apply_init_firebase_patches


class TestPushService(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.applied_patches = apply_init_firebase_patches()

    def setUp(self):
        self.push_service = PushService()

    @override_settings(MAX_DEVICES_PER_REQUEST=6)
    def test_batch_messages_single(self):
        # Test that the batch_messages method correctly batches messages
        messages = [1, 2, 3, 4, 5]
        batched_messages = self.push_service._batch_messages(messages)
        self.assertEqual(len(batched_messages), 1)
        self.assertEqual(batched_messages[0], [1, 2, 3, 4, 5])

    @override_settings(MAX_DEVICES_PER_REQUEST=3)
    def test_batch_messages_multiple(self):
        # Test that the batch_messages method correctly batches messages
        messages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        batched_messages = self.push_service._batch_messages(messages)
        self.assertEqual(len(batched_messages), 4)
        self.assertEqual(batched_messages[0], [1, 2, 3])
        self.assertEqual(batched_messages[1], [4, 5, 6])
        self.assertEqual(batched_messages[2], [7, 8, 9])
        self.assertEqual(batched_messages[3], [10])

    @patch("firebase_admin.messaging.send_each")
    def test_push_success(self, mock_send_each):
        device = baker.make(Device, firebase_token="test_token")
        notification = baker.make(
            Notification, device=device, context={"key": "value"}, image=None
        )
        mock_send_each.return_value.failure_count = 0

        self.push_service.push([notification])
        mock_send_each.assert_called_once()

    @patch("firebase_admin.messaging.send_each")
    @override_settings(MAX_DEVICES_PER_REQUEST=3)
    def test_push_success_batches(self, mock_send_each):
        device = baker.make(Device, firebase_token="test_token")
        notification = baker.make(
            Notification, device=device, context={"key": "value"}, image=None
        )
        notifications = [notification] * 8
        mock_send_each.return_value.failure_count = 0

        failed_token_count = self.push_service.push(notifications)

        self.assertEqual(mock_send_each.call_count, 3)
        self.assertEqual(failed_token_count, 0)

    @patch("firebase_admin.messaging.send_each")
    @override_settings(MAX_DEVICES_PER_REQUEST=3)
    def test_push_failed_tokens(self, mock_send_each):
        device = baker.make(Device, firebase_token="test_token")
        notification = baker.make(
            Notification, device=device, context={"key": "value"}, image=None
        )
        notifications = [notification] * 8
        mock_send_each.return_value.failure_count = 2

        failed_token_count = self.push_service.push(notifications)

        self.assertEqual(mock_send_each.call_count, 3)
        self.assertEqual(failed_token_count, 6)
