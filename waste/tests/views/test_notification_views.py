import responses
from django.conf import settings
from django.urls import reverse

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import WasteDevice


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
        resp = responses.post(
            settings.NOTIFICATION_ENDPOINT["WASTE"],
            status=201,
            json={"status": "success"},
        )
        response = self.client.post(self.url, data=payload, headers=self.api_headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(resp.call_count, 1)


class TestWasteGuideNotificationDetailView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.notification = WasteDevice.objects.create(
            bag_nummeraanduiding_id="1091",
            device_id="test-device-id",
        )
        self.api_headers["DeviceId"] = self.notification.device_id
        self.url = reverse(
            "waste-guide-notification-detail",
        )
        self.notification_url = settings.NOTIFICATION_ENDPOINT["WASTE"]

    def test_retrieve_success(self):
        resp = responses.get(
            self.notification_url, status=200, json={"status": "success"}
        )
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

    def test_retrieve_no_content(self):
        headers = {**self.api_headers, **{"DeviceId": "something-different"}}
        resp = responses.get(
            self.notification_url,
            status=200,
            json={"status": "error", "message": "not found"},
        )
        response = self.client.get(self.url, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "error", "message": "not found"})
        self.assertEqual(resp.call_count, 1)

    def test_update_success(self):
        payload = {
            "bag_nummeraanduiding_id": "1012",
        }
        resp = responses.post(self.notification_url, status=200, json=payload)
        response = self.client.patch(self.url, data=payload, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            responses.calls[0].response.json()["bag_nummeraanduiding_id"],
            payload["bag_nummeraanduiding_id"],
        )
        self.assertEqual(resp.call_count, 1)

    def test_delete_success(self):
        resp = responses.delete(self.notification_url, status=204)
        response = self.client.delete(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(resp.call_count, 1)

    def test_delete_not_found(self):
        headers = {**self.api_headers, **{"DeviceId": "something-different"}}
        resp = responses.delete(self.notification_url, status=204)
        response = self.client.delete(self.url, headers=headers)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(resp.call_count, 1)
