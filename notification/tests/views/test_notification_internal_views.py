import json
import pathlib
from unittest.mock import patch

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase

from notification.models import Device, Notification
from notification.utils.patch_utils import (
    MockFirebaseSendEach,
    apply_init_firebase_patches,
)

ROOT_DIR = pathlib.Path(__file__).resolve().parents[3]


@patch("notification.services.push.messaging.send_each")
class NotificationCreateViewTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("notification-create-notification")
        self.firebase_paths = apply_init_firebase_patches()

    def test_init_notification_success(self, mock_send_each):
        device = baker.make(Device, external_id="abc", firebase_token="abc_token")
        data = {
            "title": "foobar title",
            "body": "foobar body",
            "module_slug": "foobar module slug",
            "context": {"foo": "bar"},
            "created_at": "2024-10-31T15:00:00",
            "device_ids": ["abc", "def", "ghi"],
        }
        messages = mock_send_each([device], title=data["title"], body=data["body"])
        mock_send_each.return_value = MockFirebaseSendEach(messages)

        result = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        response = result.json()
        self.assertEqual(
            response,
            {
                "devices_with_token_count": 1,
                "failed_token_count": 0,
                "total_device_count": 3,
                "unknown_device_count": 2,
            },
        )

    def test_init_notification_with_image_success(self, _):
        image_id = 3
        data = {
            "title": "foobar title",
            "body": "foobar body",
            "module_slug": "foobar module slug",
            "context": {"foo": "bar"},
            "created_at": "2024-10-31T15:00:00",
            "device_ids": ["abc", "def", "ghi"],
            "image": image_id,
        }

        result = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        response = result.json()
        self.assertEqual(
            response,
            {
                "devices_with_token_count": 0,
                "failed_token_count": 0,
                "total_device_count": 3,
                "unknown_device_count": 3,
            },
        )
        notifications = Notification.objects.all()
        self.assertEqual(notifications[0].image, image_id)

    @override_settings(MAX_DEVICES_PER_REQUEST=5)
    def test_too_many_devices(self, _):
        data = {
            "title": "foobar",
            "body": "something",
            "context_json": {"foo": "bar"},
            "created_at": "2024-10-31T15:00:00",
            "device_ids": [
                f"device_{i}" for i in range(settings.MAX_DEVICES_PER_REQUEST + 1)
            ],
        }
        result = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Too many device ids", result.content.decode())
