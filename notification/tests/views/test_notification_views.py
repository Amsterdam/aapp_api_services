from datetime import datetime, timedelta
from unittest.mock import patch

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

from core.tests.test_authentication import BasicAPITestCase
from notification.crud import NotificationCRUD
from notification.models import Device, Notification
from notification.utils.patch_utils import apply_init_firebase_patches


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
        image_id = 123
        mock_service_instance = mock_image_set_service.return_value
        mock_service_instance.get.return_value = {
            "id": image_id,
            "variants": [
                {"image": "https://example.com/image.jpg", "width": 100, "height": 100}
            ],
        }

        device = baker.make(Device, external_id=self.device_id)
        notification_with_image = baker.make(
            Notification, device=device, image=image_id
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
                self.assertEqual(notification["image"]["id"], image_id)
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


TEST_SCOPE_1, TEST_SCOPE_2, TEST_SCOPE_NOTIFICATION_TYPE = (
    "mijn-amsterdam:scope-1",
    "mijn-amsterdam:scope-2",
    "mijn-amsterdam:type",
)


@override_settings(
    NOTIFICATION_SCOPES=[TEST_SCOPE_1, TEST_SCOPE_2, TEST_SCOPE_NOTIFICATION_TYPE]
)
class NotificationLastViewTests(BaseNotificationViewGetTestCase):
    test_slug = "mijn-amsterdam"
    test_type = "mijn-amsterdam:type"

    def setUp(self):
        super().setUp()
        self.base_notification = baker.make(Notification)
        self.device = baker.make(Device, external_id=self.device_id)
        self.other_device = baker.make(Device, external_id="999")
        self.url = reverse("notification-last")
        self.firebase_paths = apply_init_firebase_patches()

    def test_success(self):
        self._create_notification(device_id=self.device_id)

        response = self.client.get(
            self.url, query_params=self._params(), headers=self.headers_with_device_id
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["notification_scope"], TEST_SCOPE_NOTIFICATION_TYPE
        )

    def test_missing_module_slug_returns_400(self):
        response = self.client.get(self.url, headers=self.headers_with_device_id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_get_own_device(self):
        self._create_notification(device_id=self.other_device.external_id)

        response = self.client.get(
            self.url, query_params=self._params(), headers=self.headers_with_device_id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        headers_other = {
            **self.headers_with_device_id,
            settings.HEADER_DEVICE_ID: self.other_device.external_id,
        }
        response = self.client.get(
            self.url, query_params=self._params(), headers=headers_other
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_other_scope_not_active(self):
        self._create_notification(
            device_id=self.device_id,
            module_slug="other_module",
            notification_type="other_module:type",
        )

        response = self.client.get(
            self.url,
            query_params=self._params(slug="other_module"),
            headers=self.headers_with_device_id,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_multiple_scopes(self):
        self._create_notification(device_id=self.device_id)
        self._create_notification(
            device_id=self.device_id,
            notification_scope=TEST_SCOPE_1,
        )
        self._create_notification(
            device_id=self.device_id, notification_scope=TEST_SCOPE_2
        )

        response = self.client.get(
            self.url, query_params=self._params(), headers=self.headers_with_device_id
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        scopes = {n["notification_scope"] for n in response.data}
        self.assertSetEqual(
            scopes, {TEST_SCOPE_NOTIFICATION_TYPE, TEST_SCOPE_1, TEST_SCOPE_2}
        )

    def test_timestamp_updated(self):
        self._create_notification(device_id=self.device_id)

        response = self.client.get(
            self.url, query_params=self._params(), headers=self.headers_with_device_id
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        first_timestamp = datetime.fromisoformat(response.data[0]["last_create"])
        self.assertLess(first_timestamp, timezone.now())

        # Now create a new notification and check if the timestamp is updated
        self._create_notification(device_id=self.device_id)
        response = self.client.get(
            self.url, query_params=self._params(), headers=self.headers_with_device_id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        second_timestamp = datetime.fromisoformat(response.data[0]["last_create"])
        self.assertGreater(second_timestamp, first_timestamp)

    def _create_notification(
        self,
        device_id,
        module_slug="mijn-amsterdam",
        notification_type="mijn-amsterdam:type",
        notification_scope=None,
    ):
        """Helper method to create a notification for testing."""
        device_qs = Device.objects.filter(external_id=device_id)
        notification = baker.make(
            Notification,
            device=device_qs.first(),
            module_slug=module_slug,
            notification_type=notification_type,
        )
        notification_crud = NotificationCRUD(
            notification, notification_scope=notification_scope
        )
        notification_crud.create(device_qs)

    def _params(self, slug="mijn-amsterdam"):
        return {"module_slug": slug}
