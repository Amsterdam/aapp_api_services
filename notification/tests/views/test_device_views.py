from django.conf import settings
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from core.authentication import APIKeyAuthentication
from core.enums import Service
from core.exceptions import MissingDeviceIdHeader
from core.tests.test_authentication import AuthenticatedAPITestCase
from notification.models import (
    Device,
    NotificationPushServiceEnabled,
    NotificationPushTypeEnabled,
)


class TestDeviceRegisterView(AuthenticatedAPITestCase):
    authentication_class = APIKeyAuthentication

    def setUp(self):
        super().setUp()
        self.device_id = "test_device_id"
        self.headers_with_device_id = {
            settings.HEADER_DEVICE_ID: self.device_id,
            **self.api_headers,
        }
        self.url = reverse("notification-register-device")

    def test_registration_ok(self):
        """Test registering a new device"""
        data = {"firebase_token": "foobar_token", "os": "ios"}

        # First registration
        response = self.client.post(self.url, data, headers=self.headers_with_device_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["firebase_token"], data["firebase_token"])
        self.assertEqual(response.data["os"], data["os"])

        # Silent discard second call
        response = self.client.post(self.url, data, headers=self.headers_with_device_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["firebase_token"], data["firebase_token"])
        self.assertEqual(response.data["os"], data["os"])

        # Assert only one record in db
        devices_with_token = Device.objects.filter(firebase_token__isnull=False)
        self.assertEqual(devices_with_token.count(), 1)

    def test_delete_registration(self):
        """Test removing a device registration"""
        device_id = "foobar_device"
        baker.make(
            Device, external_id=device_id, firebase_token="foobar_token", os="os"
        )

        # Delete registration
        headers = {settings.HEADER_DEVICE_ID: device_id, **self.api_headers}
        response = self.client.delete(self.url, headers=headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, "Registration removed")

        # Expect no records in db
        device_from_db = Device.objects.get(external_id=device_id)
        self.assertIsNone(device_from_db.firebase_token)

        # Silently discard not existing registration delete
        response = self.client.delete(self.url, headers=headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, "Registration removed")

    def test_delete_no_device(self):
        headers = {
            settings.HEADER_DEVICE_ID: "non-existing-device-id",
            **self.api_headers,
        }
        response = self.client.delete(self.url, headers=headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_missing_os(self):
        """Test if missing OS is detected"""
        data = {"firebase_token": "0"}
        response = self.client.post(self.url, data, headers=self.headers_with_device_id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_firebase_token(self):
        """Test if missing token is detected"""
        data = {"os": "ios"}
        response = self.client.post(self.url, data, headers=self.headers_with_device_id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_device_id(self):
        """Test if missing device identifier is detected"""
        data = {"firebase_token": "0", "os": "ios"}
        response = self.client.post(self.url, data, headers=self.api_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestNotificationPushEnabledView(AuthenticatedAPITestCase):
    authentication_class = APIKeyAuthentication

    def setUp(self):
        super().setUp()
        self.url = reverse("notification-device-push-type-enabled")
        self.device = baker.make(
            Device, external_id="test-device-id", firebase_token="test-token", os="ios"
        )
        self.valid_notification_type = "test-notification-type"
        self.headers_with_device_id = {
            settings.HEADER_DEVICE_ID: self.device.external_id,
            **self.api_headers,
        }

    def test_enable_push_notification_success(self):
        """Test successfully enabling push notifications for a type."""
        data = {"notification_type": self.valid_notification_type}
        response = self.client.post(self.url, data, headers=self.headers_with_device_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["notification_type"], self.valid_notification_type
        )
        self.assertTrue(
            NotificationPushTypeEnabled.objects.filter(
                device=self.device, notification_type=self.valid_notification_type
            ).exists()
        )

    def test_enable_push_notification_duplicate(self):
        """Test enabling an already enabled notification type."""
        baker.make(
            NotificationPushTypeEnabled,
            device=self.device,
            notification_type=self.valid_notification_type,
        )

        data = {"notification_type": self.valid_notification_type}
        response = self.client.post(self.url, data, headers=self.headers_with_device_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            NotificationPushTypeEnabled.objects.filter(
                device=self.device, notification_type=self.valid_notification_type
            ).count(),
            1,
        )

    def test_enable_push_notification_missing_device_id(self):
        """Test enabling push notifications without device ID header."""
        data = {"notification_type": self.valid_notification_type}
        response = self.client.post(self.url, data, headers=self.api_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], MissingDeviceIdHeader.default_detail)

    def test_enable_push_notification_invalid_device(self):
        """Test enabling push notifications for non-existent device."""
        headers = {settings.HEADER_DEVICE_ID: "non-existent-device", **self.api_headers}
        data = {"notification_type": self.valid_notification_type}
        response = self.client.post(self.url, data, headers=headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertContains(
            response, "No Device matches the given query", status_code=404
        )

    def test_disable_push_notification_success(self):
        """Test successfully disabling push notifications for a type."""
        baker.make(
            NotificationPushTypeEnabled,
            device=self.device,
            notification_type=self.valid_notification_type,
        )

        url = f"{self.url}?notification_type={self.valid_notification_type}"
        response = self.client.delete(url, headers=self.headers_with_device_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            NotificationPushTypeEnabled.objects.filter(
                device=self.device, notification_type=self.valid_notification_type
            ).exists()
        )

    def test_disable_push_notification_not_found(self):
        """Test disabling a non-existent push notification configuration."""
        url = f"{self.url}?notification_type={self.valid_notification_type}"
        response = self.client.delete(url, headers=self.headers_with_device_id)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertContains(
            response,
            "No NotificationPushTypeEnabled matches the given query",
            status_code=404,
        )

    def test_disable_push_notification_missing_type(self):
        """Test disabling push notifications without specifying type."""
        response = self.client.delete(self.url, headers=self.headers_with_device_id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(response, "Notification type is required", status_code=400)


class TestNotificationPushEnabledListView(AuthenticatedAPITestCase):
    authentication_class = APIKeyAuthentication

    def setUp(self):
        super().setUp()
        self.url = reverse("notification-device-push-type-enabled-list")
        self.device = baker.make(
            Device, external_id="test-device-id", firebase_token="test-token", os="ios"
        )
        self.headers = {
            settings.HEADER_DEVICE_ID: self.device.external_id,
            **self.api_headers,
        }
        self.notification_types = ["type1", "type2", "type3"]

    def test_list_enabled_notifications_empty(self):
        """Test listing enabled notifications when none exist."""
        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_enabled_notifications_success(self):
        """Test listing multiple enabled notifications."""
        # Create some enabled notifications
        for notification_type in self.notification_types:
            baker.make(
                NotificationPushTypeEnabled,
                device=self.device,
                notification_type=notification_type,
            )

        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.notification_types))
        self.assertEqual(sorted(response.data), sorted(self.notification_types))

    def test_list_enabled_notifications_missing_device_id(self):
        """Test listing notifications without device ID header."""
        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], MissingDeviceIdHeader.default_detail)

    def test_list_enabled_notifications_invalid_device(self):
        """Test listing notifications for non-existent device."""
        headers = {settings.HEADER_DEVICE_ID: "non-existent-device", **self.api_headers}
        response = self.client.get(self.url, headers=headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_enabled_notifications_other_device(self):
        """Test that notifications from other devices are not included."""
        # Create another device with notifications
        other_device = baker.make(
            Device,
            external_id="other-device-id",
            firebase_token="other-token",
            os="android",
        )
        baker.make(
            NotificationPushTypeEnabled,
            device=other_device,
            notification_type="other-type",
        )

        # Create notification for test device
        baker.make(
            NotificationPushTypeEnabled,
            device=self.device,
            notification_type="test-type",
        )

        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0], "test-type")


class TestNotificationPushServiceEnabledView(AuthenticatedAPITestCase):
    authentication_class = APIKeyAuthentication

    def setUp(self):
        super().setUp()
        self.url = reverse("notification-device-push-service-enabled")
        self.device = baker.make(
            Device, external_id="test-device-id", firebase_token="test-token", os="ios"
        )
        self.headers = {
            settings.HEADER_DEVICE_ID: self.device.external_id,
            **self.api_headers,
        }
        self.service_names = [service.value for service in Service]

    def test_enable_push_service_success(self):
        """Test successfully enabling push notifications for a service."""
        service_name = self.service_names[0]
        data = {"service_name": service_name}
        response = self.client.post(self.url, data, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["service_name"], service_name)
        self.assertTrue(
            NotificationPushServiceEnabled.objects.filter(
                device=self.device, service_name=service_name
            ).exists()
        )

    def test_enable_push_service_duplicate(self):
        """Test enabling an already enabled service."""
        baker.make(
            NotificationPushServiceEnabled,
            device=self.device,
            service_name=self.service_names[0],
        )

        data = {"service_name": self.service_names[0]}
        response = self.client.post(self.url, data, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            NotificationPushServiceEnabled.objects.filter(
                device=self.device, service_name=self.service_names[0]
            ).count(),
            1,
        )

    def test_unknown_service_name(self):
        """Test enabling push notifications for an unknown service."""
        unknown_service_name = "unknown-service-name"
        data = {"service_name": unknown_service_name}
        response = self.client.post(self.url, data, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_enable_push_service_missing_device_id(self):
        """Test enabling push notifications without device ID header."""
        data = {"service_name": self.service_names[0]}
        response = self.client.post(self.url, data, headers=self.api_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_disable_push_service_success(self):
        """Test successfully disabling push notifications for a service."""
        baker.make(
            NotificationPushServiceEnabled,
            device=self.device,
            service_name=self.service_names[0],
        )

        url = f"{self.url}?service_name={self.service_names[0]}"
        response = self.client.delete(url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            NotificationPushServiceEnabled.objects.filter(
                device=self.device, service_name=self.service_names[0]
            ).exists()
        )

    def test_disable_push_service_service_name_not_found(self):
        """Test disabling push notifications for a non-existent service."""
        url = f"{self.url}?service_name={self.service_names[0]}"
        response = self.client.delete(url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_disable_push_service_missing_service_name(self):
        """Test disabling push notifications without specifying service name."""
        response = self.client.delete(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(response, "Service name is required", status_code=400)


class TestNotificationPushServiceEnabledListView(AuthenticatedAPITestCase):
    authentication_class = APIKeyAuthentication

    def setUp(self):
        super().setUp()
        self.url = reverse("notification-device-push-service-enabled-list")
        self.device = baker.make(
            Device, external_id="test-device-id", firebase_token="test-token", os="ios"
        )
        self.headers = {
            settings.HEADER_DEVICE_ID: self.device.external_id,
            **self.api_headers,
        }
        self.service_names = [service.value for service in Service]

    def test_list_enabled_services_empty(self):
        """Test listing enabled services when none exist."""
        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_enabled_services_success(self):
        """Test listing multiple enabled services."""
        # Create some enabled services
        for service_name in self.service_names:
            baker.make(
                NotificationPushServiceEnabled,
                device=self.device,
                service_name=service_name,
            )

        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.service_names))
        self.assertEqual(sorted(response.data), sorted(self.service_names))

    def test_list_enabled_services_missing_device_id(self):
        """Test listing enabled services without device ID header."""
        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], MissingDeviceIdHeader.default_detail)

    def test_list_enabled_services_invalid_device(self):
        """Test listing enabled services for non-existent device."""
        headers = {settings.HEADER_DEVICE_ID: "non-existent-device", **self.api_headers}
        response = self.client.get(self.url, headers=headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
