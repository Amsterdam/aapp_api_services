import responses
from django.conf import settings
from django.urls import reverse

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import BurningGuideDevice


class TestBurningGuideNotificationCreateView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("burning-guide-notification-create")
        self.device_id = "test-device-id"
        self.api_headers["DeviceId"] = self.device_id

    def test_success(self):
        payload = {
            "postal_code": "1023",
        }
        resp = responses.post(
            settings.NOTIFICATION_ENDPOINT["BURNING_GUIDE"],
            status=201,
            json={"status": "success"},
        )
        response = self.client.post(self.url, data=payload, headers=self.api_headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(resp.call_count, 1)


class TestBurningGuideNotificationDetailView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.notification = BurningGuideDevice.objects.create(
            postal_code="1023",
            device_id="test-device-id",
        )
        self.api_headers["DeviceId"] = self.notification.device_id
        self.url = reverse(
            "burning-guide-notification",
        )
        self.notification_url = settings.NOTIFICATION_ENDPOINT["BURNING_GUIDE"]

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
            "postal_code": "1024",
        }
        resp = responses.post(self.notification_url, status=200, json=payload)
        response = self.client.patch(self.url, data=payload, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            responses.calls[0].response.json()["postal_code"],
            payload["postal_code"],
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
