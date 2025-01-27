import json
import pathlib
from os.path import join
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase

from notification.models import Device, ImageSet, ImageVariant, Notification
from notification.utils.patch_utils import (
    MockFirebaseSendEach,
    apply_init_firebase_patches,
)

ROOT_DIR = pathlib.Path(__file__).resolve().parents[3]


def get_image_file():
    filepath = join(ROOT_DIR, "notification/tests/views/example.jpg")
    with open(filepath, "rb") as image_file:
        file = SimpleUploadedFile(
            name="example.jpg",
            content=image_file.read(),
            content_type="image/jpeg",
        )
    return file


class ImageSetCreateViewTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("notification-create-image")

    @override_settings(DEFAULT_FILE_STORAGE="django.core.files.storage.InMemoryStorage")
    def test_create_imageset_success(self):
        file = get_image_file()
        payload = {"description": "Test", "image": file}
        response = self.client.post(self.url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("id", response.data)
        self.assertIn("variants", response.data)
        self.assertIn("description", response.data)

    def test_create_imageset_missing_image(self):
        response = self.client.post(
            self.url, {"description": "Test"}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image", response.data)

    def test_create_imageset_invalid_file(self):
        payload = {"description": "Invalid file", "image": "not_an_image"}
        response = self.client.post(self.url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image", response.data)


@patch("notification.services.push.messaging.send_each")
class NotificationCreateViewTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("notification-create-notification")
        self.firebase_pathes = apply_init_firebase_patches()

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

    @override_settings(DEFAULT_FILE_STORAGE="django.core.files.storage.InMemoryStorage")
    def test_init_notification_with_image_success(self, _):
        imagevariant = baker.make(ImageVariant, image=get_image_file())
        imageset = baker.make(
            ImageSet,
            image_small=imagevariant,
            image_medium=imagevariant,
            image_large=imagevariant,
        )
        data = {
            "title": "foobar title",
            "body": "foobar body",
            "module_slug": "foobar module slug",
            "context": {"foo": "bar"},
            "created_at": "2024-10-31T15:00:00",
            "device_ids": ["abc", "def", "ghi"],
            "image": imageset.id,
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
        self.assertEqual(notifications[0].image_set, imageset)

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
