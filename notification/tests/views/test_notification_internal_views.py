import json
import pathlib
from unittest.mock import Mock, patch

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from rest_framework import status

from core.tests.test_authentication import BasicAPITestCase
from notification.models import Device, Notification, ScheduledNotification
from notification.utils.patch_utils import (
    MockFirebaseSendEach,
    apply_init_firebase_patches,
)

ROOT_DIR = pathlib.Path(__file__).resolve().parents[3]


@patch("notification.services.push.messaging.send_each")
class NotificationCreateViewTests(BasicAPITestCase):
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
            "notification_type": "foobar-notification-type",
        }
        messages = mock_send_each([device], title=data["title"], body=data["body"])
        mock_send_each.return_value = MockFirebaseSendEach(messages)

        result = self.client.post(
            self.url,
            data=json.dumps(data),
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(
            result.json(),
            {
                "total_device_count": 3,
                "total_token_count": 1,
                "total_enabled_count": 1,
                "failed_token_count": 0,
            },
        )

    @patch("notification.serializers.notification_serializers.ImageSetService")
    def test_init_notification_with_image_success(self, mock_image_service, _):
        instance_image_service = mock_image_service.return_value
        instance_image_service.exists.return_value = True
        image_id = 3
        data = {
            "title": "foobar title",
            "body": "foobar body",
            "module_slug": "foobar module slug",
            "context": {"foo": "bar"},
            "created_at": "2024-10-31T15:00:00",
            "device_ids": ["abc", "def", "ghi"],
            "notification_type": "foobar-notification-type",
            "image": image_id,
        }

        result = self.client.post(
            self.url,
            data=json.dumps(data),
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        response = result.json()
        self.assertEqual(
            response,
            {
                "total_device_count": 3,
                "total_token_count": 0,
                "total_enabled_count": 0,
                "failed_token_count": 0,
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
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Too many device ids", result.content.decode())


class ScheduledNotificationBase(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("notification-scheduled-notification")
        self.firebase_paths = apply_init_firebase_patches()
        device_ids = ["abc", "def", "ghi"]
        [baker.make(Device, external_id=external_id) for external_id in device_ids]
        self.identifier = "foobar-identifier"
        self.notification_payload = {
            "title": "foobar title",
            "body": "foobar body",
            "module_slug": "foobar",
            "context": {"foo": "bar"},
            "created_at": "2024-10-31T15:00:00",
            "device_ids": device_ids,
            "notification_type": "foobar-notification-type",
            "scheduled_for": timezone.now() + timezone.timedelta(days=1),
            "identifier": self.identifier,
        }

    def client_post(self, payload):
        payload = payload.copy()
        payload["scheduled_for"] = payload["scheduled_for"].isoformat()
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            headers=self.api_headers,
            content_type="application/json",
        )


class ScheduledNotificationTests(ScheduledNotificationBase):
    def setUp(self):
        super().setUp()
        self.url = reverse("notification-scheduled-notification")

    def test_create_scheduled_notification_success(self):
        response = self.client_post(self.notification_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            ScheduledNotification.objects.filter(identifier=self.identifier).exists()
        )

    def test_create_scheduled_notification_in_the_past(self):
        payload = self.notification_payload.copy()
        payload["scheduled_for"] = timezone.now() - timezone.timedelta(days=1)
        response = self.client_post(payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("SCHEDULED_NOTIFICATION_IN_PAST", response.content.decode())

    def test_create_scheduled_notification_duplicate_identifier(self):
        response = self.client_post(self.notification_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            ScheduledNotification.objects.filter(identifier=self.identifier).exists()
        )

        response = self.client_post(self.notification_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "SCHEDULED_NOTIFICATION_DUPLICATE_IDENTIFIER", response.content.decode()
        )

    def test_create_scheduled_notification_missing_device_id(self):
        payload = self.notification_payload.copy()
        payload["device_ids"] += ["missing_device_id"]
        response = self.client_post(self.notification_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            ScheduledNotification.objects.filter(identifier=self.identifier).exists()
        )
        self.assertTrue(Device.objects.filter(external_id="missing_device_id").exists())
        scheduled_devices = ScheduledNotification.objects.get(
            identifier=self.identifier
        ).devices.all()
        self.assertEqual(scheduled_devices.count(), 4)

    def test_create_scheduled_notification_identifier_must_start_with_module_slug(self):
        payload = self.notification_payload.copy()
        payload["identifier"] = "wrong-identifier-234"
        response = self.client_post(payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("SCHEDULED_NOTIFICATION_IDENTIFIER", response.content.decode())

    @patch("notification.serializers.notification_serializers.ImageSetService")
    def test_create_scheduled_notification_with_image(self, mock_image_service):
        instance_image_service = mock_image_service.return_value
        instance_image_service.exists.return_value = True
        payload = self.notification_payload.copy()
        payload["image"] = 123

        response = self.client_post(payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        saved_notification = ScheduledNotification.objects.get(
            identifier=self.identifier
        )
        self.assertEqual(saved_notification.image, 123)

    @patch("notification.serializers.notification_serializers.ImageSetService")
    def test_create_scheduled_notification_with_image_does_not_exist(
        self, mock_image_service
    ):
        instance_image_service = mock_image_service.return_value
        instance_image_service.exists.return_value = False
        payload = self.notification_payload.copy()
        payload["image"] = 123

        response = self.client_post(payload)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("IMAGE_SET_NOT_FOUND", response.content.decode())

    @override_settings(MAX_DEVICES_PER_REQUEST=2)
    def test_create_scheduled_notification_too_many_devices(self):
        response = self.client_post(self.notification_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Too many device ids", response.content.decode())

    def test_list_scheduled_notifications(self):
        baker.make(ScheduledNotification, _quantity=5)
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 5)


class ScheduledNotificationDetailTests(ScheduledNotificationBase):
    def setUp(self):
        super().setUp()
        self.url = reverse("notification-scheduled-notification")
        response = self.client_post(self.notification_payload)
        self.url = reverse(
            "notification-scheduled-notification-detail",
            kwargs={"identifier": self.identifier},
        )
        print(response.json())

    def test_retrieve_scheduled_notification_success(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["title"], self.notification_payload["title"])

    def test_update_scheduled_notification_success(self):
        patch_data = {"title": "Updated Title"}
        response = self.client.patch(
            self.url,
            data=json.dumps(patch_data),
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["title"], "Updated Title")

    def test_update_scheduled_notification_already_pushed(self):
        notification = ScheduledNotification.objects.get(identifier=self.identifier)
        notification.pushed_at = timezone.now()
        notification.save()
        patch_data = {"title": "Updated Title"}
        response = self.client.patch(
            self.url,
            data=json.dumps(patch_data),
            headers=self.api_headers,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_scheduled_notification_success(self):
        response = self.client.delete(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            ScheduledNotification.objects.filter(identifier=self.identifier).exists()
        )

    def test_delete_scheduled_notification_already_pushed(self):
        notification = ScheduledNotification.objects.get(identifier=self.identifier)
        notification.pushed_at = timezone.now()
        notification.save()
        response = self.client.delete(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@patch("notification.services.push.messaging.send_each")
class NotificationAggregateViewTests(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("notification-aggregate-notification")
        self.firebase_paths = apply_init_firebase_patches()

    def test_aggregate_notification_success_1(self, mock_send_each):
        self._run_aggregate_notification_test(mock_send_each, notification_count=1)

    def test_aggregate_notification_success_2(self, mock_send_each):
        self._run_aggregate_notification_test(mock_send_each, notification_count=2)

    def test_aggregate_notification_success_3(self, mock_send_each):
        self._run_aggregate_notification_test(mock_send_each, notification_count=3)

    def _run_aggregate_notification_test(self, mock_send_each, notification_count):
        baker.make(Device, external_id="abc", firebase_token="abc_token")
        data = [
            {
                "title": "foobar title",
                "body": "foobar body",
                "module_slug": "foobar module slug",
                "context": {"foo": "bar"},
                "created_at": "2024-10-31T15:00:00",
                "device_ids": ["abc", "def", "ghi"],
                "notification_type": "foobar-notification-type",
            }
            for _ in range(notification_count)
        ]
        firebase_response = Mock()
        firebase_response.failure_count = 0
        mock_send_each.return_value = firebase_response

        result = self.client.post(
            self.url,
            data=json.dumps(data),
            headers=self.api_headers,
            content_type="application/json",
        )

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(
            result.json(),
            [
                {
                    "total_device_count": 3,
                    "total_token_count": 1,
                    "total_enabled_count": 1,
                    "failed_token_count": 0,
                }
                for _ in range(notification_count)
            ],
        )
        # Assert number of created notifications
        created_count = Notification.objects.count()
        self.assertEqual(created_count, 3 * notification_count)

        # Assert send_each was called ONCE with the correct body
        mock_send_each.assert_called_once()
        args, _ = mock_send_each.call_args
        notification = args[0][0].notification
        self.assertEqual(
            notification.body, f"Er staan {notification_count} berichten voor je klaar"
        )
