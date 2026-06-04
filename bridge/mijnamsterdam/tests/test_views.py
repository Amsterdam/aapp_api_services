from unittest.mock import patch

import responses
from django.conf import settings
from django.urls import reverse

from bridge.mijnamsterdam.tests.mock_data.is_registered import (
    IS_REGISTERED_FALSE,
    IS_REGISTERED_TRUE,
)
from bridge.mijnamsterdam.tests.mock_data.logout import (
    IS_DELETED_FALSE,
    IS_DELETED_TRUE,
)
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import ScheduledNotification


class TestMijnAmsterdamDeviceView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("mijn-amsterdam-device")
        self.device_id = "test-device-id"
        self.api_headers["DeviceId"] = self.device_id

    def test_success_get(self):
        url = self._get_mijnams_url(self.device_id)
        responses.add(responses.GET, url, json=IS_REGISTERED_TRUE, status=200)

        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"status": "OK", "profile_name": "J.M. Stephenson"}
        )

    def test_success_delete(self):
        url = self._get_mijnams_url(self.device_id)
        responses.add(responses.DELETE, url, json=IS_DELETED_TRUE, status=200)

        response = self.client.delete(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "OK"})

    def test_success_get_does_not_exist(self):
        url = self._get_mijnams_url(self.device_id)
        responses.add(responses.GET, url, json=IS_REGISTERED_FALSE, status=200)

        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ERROR"})

    def test_success_delete_does_not_exist(self):
        url = self._get_mijnams_url(self.device_id)
        responses.add(responses.DELETE, url, json=IS_DELETED_FALSE, status=200)

        response = self.client.delete(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ERROR"})

    def test_timeout_get(self):
        url = self._get_mijnams_url(self.device_id)
        responses.add(
            responses.GET, url, body=responses.ConnectionError("Connection timed out")
        )

        with patch("tenacity.nap.sleep", return_value=None):
            response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 500)

    def test_one_timeout_then_success_get(self):
        url = self._get_mijnams_url(self.device_id)
        responses.add(
            responses.GET, url, body=responses.ConnectionError("Connection timed out")
        )
        responses.add(responses.GET, url, json=IS_REGISTERED_TRUE, status=200)

        with patch("tenacity.nap.sleep", return_value=None):
            response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"status": "OK", "profile_name": "J.M. Stephenson"}
        )

    def _get_mijnams_url(self, device_id):
        return (
            settings.MIJN_AMS_API_DOMAIN
            + settings.MIJN_AMS_API_PATHS["DEVICES"]
            + device_id
        )


class TestLogoutNotificationView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("mijn-amsterdam-logout-notification")

    def test_success_post(self):
        response = self.client.post(
            self.url,
            data={"device_ids": ["device-1", "device-2", "device-1"]},
            format="json",
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "OK"})
        self.assertEqual(ScheduledNotification.objects.count(), 1)
        scheduled_notification = ScheduledNotification.objects.first()
        self.assertEqual(scheduled_notification.devices.count(), 2)

    def test_post_empty_device_ids(self):
        response = self.client.post(
            self.url,
            data={"device_ids": []},
            format="json",
            headers=self.api_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "OK"})
        self.assertEqual(ScheduledNotification.objects.count(), 0)

    def test_post_unauthorized(self):
        response = self.client.post(
            self.url,
            data={"device_ids": ["device-1"]},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
