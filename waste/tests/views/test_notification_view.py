from django.urls import reverse

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from waste.models import NotificationSchedule


class TestWasteNotificationCreateView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("waste-guide-notification-create")
        self.device_id = "test-device-id"
        self.api_headers["DeviceId"] = self.device_id

    def test_success(self):
        payload = {
            "bag_nummeraanduiding_id": "12345",
        }
        response = self.client.post(self.url, data=payload, headers=self.api_headers)
        self.assertEqual(response.status_code, 201)
        NotificationSchedule.objects.get(device_id=self.device_id)


class TestBurningGuideNotificationView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.notification = NotificationSchedule.objects.create(
            bag_nummeraanduiding_id="1091",
            device_id="test-device-id",
        )
        self.api_headers["DeviceId"] = self.notification.device_id
        self.url = reverse(
            "waste-guide-notification-detail",
        )

    def test_retrieve_success(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)

    def test_retrieve_no_content(self):
        NotificationSchedule.objects.all().delete()
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "error", "message": "not found"})

    def test_update_success(self):
        payload = {
            "bag_nummeraanduiding_id": "1012",
        }
        response = self.client.patch(self.url, data=payload, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        updated_notification = NotificationSchedule.objects.get(
            device_id=self.notification.device_id
        )
        self.assertEqual(
            updated_notification.bag_nummeraanduiding_id,
            payload["bag_nummeraanduiding_id"],
        )

    def test_delete_success(self):
        response = self.client.delete(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 204)
        notification_records = NotificationSchedule.objects.all()
        self.assertEqual(notification_records.count(), 0)

    def test_delete_not_found(self):
        NotificationSchedule.objects.all().delete()
        response = self.client.delete(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 204)
