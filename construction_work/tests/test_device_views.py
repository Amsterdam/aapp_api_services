from django.conf import settings
from django.urls import reverse

from construction_work.models import Device
from core.tests import BaseAPITestCase


class TestDeviceRegisterView(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.api_url = reverse("register-device")

    def test_registration_ok(self):
        """Test registering a new device"""
        data = {"firebase_token": "foobar_token", "os": "ios"}
        self.api_headers[settings.HEADER_DEVICE_ID] = "0"
        first_result = self.client.post(self.api_url, data, headers=self.api_headers)

        self.assertEqual(first_result.status_code, 200)
        self.assertEqual(
            first_result.data.get("firebase_token"), data.get("firebase_token")
        )
        self.assertEqual(first_result.data.get("os"), data.get("os"))

        # Silent discard second call
        second_result = self.client.post(self.api_url, data, headers=self.api_headers)

        self.assertEqual(second_result.status_code, 200)
        self.assertEqual(
            second_result.data.get("firebase_token"), data.get("firebase_token")
        )
        self.assertEqual(second_result.data.get("os"), data.get("os"))

        # Assert only one record in db
        devices_with_token = list(
            Device.objects.filter(firebase_token__isnull=False).all()
        )
        self.assertEqual(len(devices_with_token), 1)

    def test_delete_registration(self):
        """Test removing a device registration"""
        new_device = Device(
            device_id="foobar_device", firebase_token="foobar_token", os="os"
        )
        new_device.save()

        # Delete registration
        self.api_headers[settings.HEADER_DEVICE_ID] = "foobar_device"
        first_result = self.client.delete(self.api_url, headers=self.api_headers)

        self.assertEqual(first_result.status_code, 200)
        self.assertEqual(first_result.data, "Registration removed")

        # Expect no records in db
        devices_with_token = list(
            Device.objects.filter(firebase_token__isnull=False).all()
        )
        self.assertEqual(len(devices_with_token), 0)

        # Silently discard not existing registration delete
        second_result = self.client.delete(self.api_url, headers=self.api_headers)

        self.assertEqual(second_result.status_code, 200)
        self.assertEqual(second_result.data, "Registration removed")

    def test_delete_no_device(self):
        self.api_headers[settings.HEADER_DEVICE_ID] = "non-existing-device-id"
        first_result = self.client.delete(self.api_url, headers=self.api_headers)

        self.assertEqual(first_result.status_code, 200)

    def test_missing_os_missing(self):
        """Test if missing OS is detected"""
        data = {"firebase_token": "0"}
        self.api_headers[settings.HEADER_DEVICE_ID] = "foobar"
        result = self.client.post(self.api_url, data, headers=self.api_headers)

        self.assertEqual(result.status_code, 400)

    def test_missing_firebase_token(self):
        """Test is missing token is detected"""
        data = {"os": "ios"}
        self.api_headers[settings.HEADER_DEVICE_ID] = "foobar"
        result = self.client.post(self.api_url, data, headers=self.api_headers)

        self.assertEqual(result.status_code, 400)

    def test_missing_device_id(self):
        """Test if missing identifier is detected"""
        data = {"firebase_token": "0", "os": "ios"}
        result = self.client.post(self.api_url, data, headers=self.api_headers)

        self.assertEqual(result.status_code, 400)
