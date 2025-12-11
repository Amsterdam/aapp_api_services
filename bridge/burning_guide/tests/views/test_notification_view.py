from django.urls import reverse

from bridge.models import BurningGuideNotification
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class TestBurningGuideNotificationCreateView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("burning-guide-notification-create")

    def test_success(self):
        payload = {
            "device_id": "test-device-id",
            "postal_code": "1091",
        }
        response = self.client.post(self.url, data=payload, headers=self.api_headers)
        self.assertEqual(response.status_code, 201)
        notification_records = BurningGuideNotification.objects.all()
        self.assertEqual(notification_records.count(), 1)

    def test_invalid_postal_code(self):
        payload = {
            "device_id": "test-device-id",
            "postal_code": "9999",
        }
        response = self.client.post(self.url, data=payload, headers=self.api_headers)
        self.assertEqual(response.status_code, 400)
        notification_records = BurningGuideNotification.objects.all()
        self.assertEqual(notification_records.count(), 0)


class TestBurningGuideNotificationView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.notification = BurningGuideNotification.objects.create(
            device_id="test-device-id",
            postal_code="1091",
        )
        self.url = reverse(
            "burning-guide-notification-detail",
            args=[self.notification.device_id],
        )

    def test_retrieve_success(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["device_id"], self.notification.device_id)

    def test_update_success(self):
        payload = {
            "postal_code": "1012",
        }
        response = self.client.patch(self.url, data=payload, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        updated_notification = BurningGuideNotification.objects.get(
            device_id=self.notification.device_id
        )
        self.assertEqual(updated_notification.postal_code, payload["postal_code"])

    def test_delete_success(self):
        response = self.client.delete(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 204)
        notification_records = BurningGuideNotification.objects.all()
        self.assertEqual(notification_records.count(), 0)
