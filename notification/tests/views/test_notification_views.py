from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

from core.tests.test_authentication import BasicAPITestCase
from notification.models import Device, Notification


class BaseNotificationViewTestCase(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.device_id = "123"
        self.headers_with_device_id = {"DeviceId": self.device_id, **self.api_headers}


class BaseNotificationViewGetTestCase(BaseNotificationViewTestCase):
    def setUp(self):
        super().setUp()
        self.image_set_service_patcher = patch(
            "notification.serializers.notification_serializers.ImageSetService"
        )
        self.mock_image_set_service = self.image_set_service_patcher.start()
        self.mock_image_set_service.return_value.json.return_value = {
            "id": "123",
            "variants": [
                {"image": "https://example.com/image.jpg", "width": 100, "height": 100}
            ],
        }

    def tearDown(self):
        super().tearDown()
        self.image_set_service_patcher.stop()


class NotificationListViewTests(BaseNotificationViewGetTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("notification-list-notifications")

    def test_list_notifications(self):
        device_1 = baker.make(Device, external_id=self.device_id)
        baker.make(Notification, device=device_1)
        baker.make(Notification, device=baker.make(Device))

        response = self.client.get(self.url, headers=self.headers_with_device_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data), 1
        )  # Only notifications for device_id "123" should be returned
        self.assertIn("title", response.data[0])
        self.assertIn("body", response.data[0])
        self.assertIn("module_slug", response.data[0])

    @patch("notification.serializers.notification_serializers.ImageSetService")
    def test_list_notifications_with_and_without_image(self, mock_image_set_service):
        def image_set_side_effect(image_id):
            if image_id is None:
                raise ValueError("Invalid image ID")
            return mock_image_set_service.return_value

        mock_image_set_service.side_effect = image_set_side_effect
        mock_image_set_service.return_value.json.return_value = {
            "id": "123",
            "variants": [
                {"image": "https://example.com/image.jpg", "width": 100, "height": 100}
            ],
        }

        device = baker.make(Device, external_id=self.device_id)
        notification_with_image = baker.make(
            Notification, device=device, image=1
        )  # notification with image
        baker.make(
            Notification, device=device, image=None
        )  # notification without image

        response = self.client.get(self.url, headers=self.headers_with_device_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Check notifications are returned with correct image data
        for notification in response.data:
            if notification["id"] == str(notification_with_image.id):
                self.assertIsNotNone(notification["image"])
                self.assertEqual(notification["image"]["id"], 123)
            else:
                self.assertIsNone(notification["image"])

    def test_list_notifications_missing_device_id(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertContains(
            response,
            "Missing header: DeviceId",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_list_notifications_order_by_created_at(self):
        device_1 = baker.make(Device, external_id=self.device_id)
        notification_1 = baker.make(
            Notification,
            title="oldest",
            device=device_1,
            created_at=timezone.now() - timedelta(days=3),
        )
        notification_2 = baker.make(
            Notification,
            title="middle",
            device=device_1,
            created_at=timezone.now() - timedelta(days=2),
        )
        notification_3 = baker.make(
            Notification,
            title="newest",
            device=device_1,
            created_at=timezone.now() - timedelta(days=1),
        )

        response = self.client.get(self.url, headers=self.headers_with_device_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]["id"], str(notification_3.id))
        self.assertEqual(response.data[1]["id"], str(notification_2.id))
        self.assertEqual(response.data[2]["id"], str(notification_1.id))


class NotificationReadViewTests(BaseNotificationViewTestCase):
    def setUp(self):
        super().setUp()
        self.test_device = baker.make(Device, external_id=self.device_id)
        self.url = reverse("notification-read-notifications")

    def test_mark_all_as_read(self):
        notification = baker.make(Notification, device=self.test_device, is_read=False)

        response = self.client.post(self.url, headers=self.headers_with_device_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIn("1 notifications marked as read.", response.data["detail"])

    def test_mark_all_as_read_5(self):
        [
            baker.make(Notification, device=self.test_device, is_read=False)
            for _ in range(5)
        ]

        response = self.client.post(self.url, headers=self.headers_with_device_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("5 notifications marked as read.", response.data["detail"])

    def test_mark_unread_as_read(self):
        [
            baker.make(Notification, device=self.test_device, is_read=False)
            for _ in range(4)
        ]
        [
            baker.make(Notification, device=self.test_device, is_read=True)
            for _ in range(3)
        ]

        response = self.client.post(self.url, headers=self.headers_with_device_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("4 notifications marked as read.", response.data["detail"])

    def test_mark_only_device_as_read(self):
        [
            baker.make(Notification, device=self.test_device, is_read=False)
            for _ in range(2)
        ]
        [
            baker.make(Notification, device=baker.make(Device), is_read=False)
            for _ in range(8)
        ]

        response = self.client.post(self.url, headers=self.headers_with_device_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("2 notifications marked as read.", response.data["detail"])

    def test_mark_all_as_read_missing_device_id(self):
        response = self.client.post(self.url, headers=self.api_headers)
        self.assertContains(
            response,
            "Missing header: DeviceId",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class NotificationDetailViewTests(BaseNotificationViewGetTestCase):
    def setUp(self):
        super().setUp()
        self.notification = baker.make(
            Notification, device=baker.make(Device, external_id="123"), is_read=False
        )
        self.url = reverse(
            "notification-detail-notification",
            kwargs={"notification_id": self.notification.id},
        )

    def test_get_notification_detail(self):
        response = self.client.get(self.url, headers=self.headers_with_device_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.notification.id))
        self.assertIn("title", response.data)
        self.assertIn("body", response.data)
        self.assertIn("module_slug", response.data)

    def test_update_notification_status(self):
        response = self.client.patch(
            self.url,
            data={"is_read": True},
            format="json",
            headers=self.headers_with_device_id,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_get_notification_status_wrong_device_id(self):
        headers = {"DeviceId": "Foobar", **self.api_headers}
        response = self.client.get(self.url, headers=headers)
        self.assertContains(
            response,
            "No Notification matches the given query.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    def test_update_notification_status_wrong_device_id(self):
        headers = {"DeviceId": "Foobar", **self.api_headers}
        response = self.client.patch(
            self.url, data={"is_read": True}, format="json", headers=headers
        )
        self.assertContains(
            response,
            "No Notification matches the given query.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    def test_update_notification_title(self):
        old_title = self.notification.title
        response = self.client.patch(
            self.url,
            data={"is_read": False, "title": "foobar"},
            format="json",
            headers=self.headers_with_device_id,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertEqual(
            self.notification.title, old_title
        )  # Title should not be updated
        self.assertFalse(self.notification.is_read)

    def test_get_notification_detail_missing_device_id(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertContains(
            response,
            "Missing header: DeviceId",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_update_notification_detail_missing_device_id(self):
        response = self.client.patch(self.url, headers=self.api_headers)
        self.assertContains(
            response,
            "Missing header: DeviceId",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
