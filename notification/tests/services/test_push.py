from unittest.mock import patch

from django.test import TestCase
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

    @patch("firebase_admin.messaging.send")
    def test_push_success(self, mock_send):
        device = baker.make(Device, firebase_token="test_token")
        notification = baker.make(Notification, device=device, image=None)

        self.push_service.push([notification])
        mock_send.assert_called_once()

    @patch("firebase_admin.messaging.send")
    def test_push_success_batches(self, mock_send):
        device = baker.make(Device, firebase_token="test_token")
        notification = baker.make(Notification, device=device, image=None)
        notifications = [notification] * 8

        self.push_service.push(notifications)

        self.assertEqual(mock_send.call_count, 8)

    @patch("firebase_admin.messaging.send")
    def test_push_failed_tokens(self, mock_send):
        device = baker.make(Device, firebase_token="test_token")
        notification = baker.make(Notification, device=device, image=None)
        notifications = [notification] * 8
        mock_send.side_effect = 3 * [Exception("test error")] + 5 * [
            "foobar-notification"
        ]

        failed_token_count = self.push_service.push(notifications)

        self.assertEqual(mock_send.call_count, 8)
        self.assertEqual(failed_token_count, 3)
