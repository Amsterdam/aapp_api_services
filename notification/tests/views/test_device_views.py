from django.conf import settings
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from core.authentication import APIKeyAuthentication
from core.enums import Module
from core.exceptions import MissingDeviceIdHeader
from core.tests.test_authentication import AuthenticatedAPITestCase
from notification.models import (
    Device,
    NotificationPushModuleDisabled,
    NotificationPushTypeDisabled,
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

    def test_update_existing_device(self):
        """Test updating an existing device"""
        baker.make(
            Device, external_id=self.device_id, firebase_token="foobar_token", os="ios1"
        )
        new_data = {"firebase_token": "foobar_token2", "os": "ios2"}
        response = self.client.post(
            self.url, new_data, headers=self.headers_with_device_id
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["firebase_token"], new_data["firebase_token"])
        self.assertEqual(response.data["os"], new_data["os"])

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


class TestNotificationPushDisabledView(AuthenticatedAPITestCase):
    authentication_class = APIKeyAuthentication

    def setUp(self):
        super().setUp()
        self.url = reverse("notification-device-push-type-disabled")
        self.device = baker.make(
            Device, external_id="test-device-id", firebase_token="test-token", os="ios"
        )
        self.valid_notification_type = "test-notification-type"
        self.headers_with_device_id = {
            settings.HEADER_DEVICE_ID: self.device.external_id,
            **self.api_headers,
        }

    def test_disable_push_notification_success(self):
        """Test successfully enabling push notifications for a type."""
        data = {"notification_type": self.valid_notification_type}
        response = self.client.post(self.url, data, headers=self.headers_with_device_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["notification_type"], self.valid_notification_type
        )
        self.assertTrue(
            NotificationPushTypeDisabled.objects.filter(
                device=self.device, notification_type=self.valid_notification_type
            ).exists()
        )

    def test_disable_push_notification_duplicate(self):
        """Test enabling an already disabled notification type."""
        baker.make(
            NotificationPushTypeDisabled,
            device=self.device,
            notification_type=self.valid_notification_type,
        )

        data = {"notification_type": self.valid_notification_type}
        response = self.client.post(self.url, data, headers=self.headers_with_device_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            NotificationPushTypeDisabled.objects.filter(
                device=self.device, notification_type=self.valid_notification_type
            ).count(),
            1,
        )

    def test_disable_push_notification_missing_device_id(self):
        """Test enabling push notifications without device ID header."""
        data = {"notification_type": self.valid_notification_type}
        response = self.client.post(self.url, data, headers=self.api_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], MissingDeviceIdHeader.default_detail)

    def test_disable_push_notification_invalid_device(self):
        """Test enabling push notifications for non-existent device."""
        headers = {settings.HEADER_DEVICE_ID: "non-existent-device", **self.api_headers}
        data = {"notification_type": self.valid_notification_type}
        response = self.client.post(self.url, data, headers=headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertContains(
            response, "No Device matches the given query", status_code=404
        )

    def test_enable_push_notification_success(self):
        """Test successfully disabling push notifications for a type."""
        baker.make(
            NotificationPushTypeDisabled,
            device=self.device,
            notification_type=self.valid_notification_type,
        )

        url = f"{self.url}?notification_type={self.valid_notification_type}"
        response = self.client.delete(url, headers=self.headers_with_device_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            NotificationPushTypeDisabled.objects.filter(
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
            "No NotificationPushTypeDisabled matches the given query",
            status_code=404,
        )

    def test_disable_push_notification_missing_type(self):
        """Test disabling push notifications without specifying type."""
        response = self.client.delete(self.url, headers=self.headers_with_device_id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(response, "Notification type is required", status_code=400)


class TestNotificationPushDisabledListView(AuthenticatedAPITestCase):
    authentication_class = APIKeyAuthentication

    def setUp(self):
        super().setUp()
        self.url = reverse("notification-device-push-type-disabled-list")
        self.device = baker.make(
            Device, external_id="test-device-id", firebase_token="test-token", os="ios"
        )
        self.headers = {
            settings.HEADER_DEVICE_ID: self.device.external_id,
            **self.api_headers,
        }
        self.notification_types = ["type1", "type2", "type3"]

    def test_list_disabled_notifications_empty(self):
        """Test listing disabled notifications when none exist."""
        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_disabled_notifications_success(self):
        """Test listing multiple disabled notifications."""
        for notification_type in self.notification_types:
            baker.make(
                NotificationPushTypeDisabled,
                device=self.device,
                notification_type=notification_type,
            )

        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.notification_types))
        self.assertEqual(sorted(response.data), sorted(self.notification_types))

    def test_list_disabled_notifications_missing_device_id(self):
        """Test listing notifications without device ID header."""
        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], MissingDeviceIdHeader.default_detail)

    def test_list_disabled_notifications_invalid_device(self):
        """Test listing notifications for non-existent device."""
        headers = {settings.HEADER_DEVICE_ID: "non-existent-device", **self.api_headers}
        response = self.client.get(self.url, headers=headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_disabled_notifications_other_device(self):
        """Test that notifications from other devices are not included."""
        # Create another device with notifications
        other_device = baker.make(
            Device,
            external_id="other-device-id",
            firebase_token="other-token",
            os="android",
        )
        baker.make(
            NotificationPushTypeDisabled,
            device=other_device,
            notification_type="other-type",
        )

        # Create notification for test device
        baker.make(
            NotificationPushTypeDisabled,
            device=self.device,
            notification_type="test-type",
        )

        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0], "test-type")


class TestNotificationPushModuleDisabledView(AuthenticatedAPITestCase):
    authentication_class = APIKeyAuthentication

    def setUp(self):
        super().setUp()
        self.url = reverse("notification-device-push-module-disabled")
        self.device = baker.make(
            Device, external_id="test-device-id", firebase_token="test-token", os="ios"
        )
        self.headers = {
            settings.HEADER_DEVICE_ID: self.device.external_id,
            **self.api_headers,
        }
        self.module_slugs = [module.value for module in Module]

    def test_disable_push_module_duplicate(self):
        """Test enabling an already disabled module."""
        baker.make(
            NotificationPushModuleDisabled,
            device=self.device,
            module_slug=self.module_slugs[0],
        )

        data = {"module_slug": self.module_slugs[0]}
        response = self.client.post(self.url, data, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            NotificationPushModuleDisabled.objects.filter(
                device=self.device, module_slug=self.module_slugs[0]
            ).count(),
            1,
        )

    def test_unknown_module_slug(self):
        """Test enabling push notifications for an unknown module. This should not raise an error."""
        unknown_module_slug = "unknown-module-name"
        data = {"module_slug": unknown_module_slug}
        response = self.client.post(self.url, data, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_disable_push_module_missing_device_id(self):
        """Test enabling push notifications without device ID header."""
        data = {"module_slug": self.module_slugs[0]}
        response = self.client.post(self.url, data, headers=self.api_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_disable_push_module_success(self):
        """Test successfully enabling push notifications for a module."""
        module_slug = self.module_slugs[0]
        data = {"module_slug": module_slug}
        response = self.client.post(self.url, data, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["module_slug"], module_slug)
        self.assertTrue(
            NotificationPushModuleDisabled.objects.filter(
                device=self.device, module_slug=module_slug
            ).exists()
        )

    def test_enable_push_module_success(self):
        """Test successfully disabling push notifications for a module."""
        baker.make(
            NotificationPushModuleDisabled,
            device=self.device,
            module_slug=self.module_slugs[0],
        )

        url = f"{self.url}?module_slug={self.module_slugs[0]}"
        response = self.client.delete(url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            NotificationPushModuleDisabled.objects.filter(
                device=self.device, module_slug=self.module_slugs[0]
            ).exists()
        )

    def test_disable_push_module_module_slug_not_found(self):
        """Test disabling push notifications for a non-existent module."""
        url = f"{self.url}?module_slug={self.module_slugs[0]}"
        response = self.client.delete(url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_disable_push_module_missing_module_slug(self):
        """Test disabling push notifications without specifying module name."""
        response = self.client.delete(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(response, "Module name is required", status_code=400)


class TestNotificationPushModuleDisabledListView(AuthenticatedAPITestCase):
    authentication_class = APIKeyAuthentication

    def setUp(self):
        super().setUp()
        self.url = reverse("notification-device-push-module-disabled-list")
        self.device = baker.make(
            Device, external_id="test-device-id", firebase_token="test-token", os="ios"
        )
        self.headers = {
            settings.HEADER_DEVICE_ID: self.device.external_id,
            **self.api_headers,
        }
        self.module_slugs = [module.value for module in Module]

    def test_list_disabled_modules_empty(self):
        """Test listing disabled modules when none exist."""
        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_disabled_modules_success(self):
        """Test listing multiple disabled modules."""
        for module_slug in self.module_slugs:
            baker.make(
                NotificationPushModuleDisabled,
                device=self.device,
                module_slug=module_slug,
            )

        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.module_slugs))
        self.assertEqual(sorted(response.data), sorted(self.module_slugs))

    def test_list_disabled_modules_missing_device_id(self):
        """Test listing disabled modules without device ID header."""
        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], MissingDeviceIdHeader.default_detail)

    def test_list_disabled_modules_invalid_device(self):
        """Test listing disabled modules for non-existent device."""
        headers = {settings.HEADER_DEVICE_ID: "non-existent-device", **self.api_headers}
        response = self.client.get(self.url, headers=headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
