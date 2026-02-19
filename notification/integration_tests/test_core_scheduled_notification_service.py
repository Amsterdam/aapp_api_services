import logging
from datetime import timedelta

import responses
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APITestCase

from core.services.scheduled_notification import (
    NotificationServiceError,
    ScheduledNotificationService,
)

logger = logging.getLogger(__name__)


class TestCoreScheduledNotificationService(APITestCase):
    def setUp(self):
        self.service = ScheduledNotificationService(use_image_service=True)
        self.created_identifiers = []

    def tearDown(self):
        for identifier in self.created_identifiers:
            try:
                self.service.delete(identifier)
            except NotificationServiceError as e:
                logger.error(
                    f"Error cleaning up integration test identifier: {identifier}: {e}"
                )

    def test_add_notification_only_required_fields(self):
        identifier = f"{settings.SERVICE_NAME}_test-notification"
        self.created_identifiers.append(identifier)

        new_scheduled_notification = self.service.upsert(
            title="Test Notification",
            body="This is a test notification",
            scheduled_for=timezone.now() + timedelta(minutes=10),
            identifier=identifier,
            context={},
            device_ids=["device1", "device2"],
            notification_type="test",
            module_slug=settings.SERVICE_NAME,
        )

        self.assertTrue(new_scheduled_notification)

    def test_add_notification_with_custom_module_slug(self):
        module_slug = "foobar-slug"
        identifier = f"{module_slug}_test-notification"
        self.created_identifiers.append(identifier)

        new_scheduled_notification = self.service.upsert(
            title="Test Notification",
            body="This is a test notification",
            scheduled_for=timezone.now() + timedelta(minutes=10),
            identifier=identifier,
            context={},
            device_ids=["device1", "device2"],
            notification_type="test",
            module_slug=module_slug,
        )

        self.assertTrue(new_scheduled_notification)

    @responses.activate
    def test_add_notification_with_unknown_image_id(self):
        identifier = f"{settings.SERVICE_NAME}_test-notification"
        self.created_identifiers.append(identifier)
        unknown_image_id = "99999999"
        responses.get(
            f"{settings.IMAGE_ENDPOINTS['DETAIL']}/{unknown_image_id}",
            status=404,
            json={},
        )

        with self.assertRaises(NotificationServiceError):
            self.service.upsert(
                title="Test Notification",
                body="This is a test notification",
                scheduled_for=timezone.now() + timedelta(minutes=10),
                identifier=identifier,
                context={},
                device_ids=["device1", "device2"],
                notification_type="test",
                image=unknown_image_id,
                module_slug=settings.SERVICE_NAME,
            )

    def test_add_notification_with_specific_expiration(self):
        identifier = f"{settings.SERVICE_NAME}_test-notification"
        self.created_identifiers.append(identifier)
        scheduled_for = timezone.now() + timedelta(minutes=10)
        expires_at = scheduled_for + timedelta(minutes=10)

        new_scheduled_notification = self.service.upsert(
            title="Test Notification",
            body="This is a test notification",
            scheduled_for=scheduled_for,
            identifier=identifier,
            context={},
            device_ids=["device1", "device2"],
            notification_type="test",
            expires_at=expires_at,
            module_slug=settings.SERVICE_NAME,
        )

        self.assertTrue(new_scheduled_notification)
        scheduled_expires_at = new_scheduled_notification.expires_at
        self.assertEqual(scheduled_expires_at.timestamp(), expires_at.timestamp())

    def test_get_notification(self):
        identifier = f"{settings.SERVICE_NAME}_test-notification"
        self.created_identifiers.append(identifier)

        self.service.upsert(
            title="Test Notification",
            body="This is a test notification",
            scheduled_for=timezone.now() + timedelta(minutes=10),
            identifier=identifier,
            context={},
            device_ids=["device1", "device2"],
            notification_type="test",
            module_slug=settings.SERVICE_NAME,
        )
        result_notification = self.service.get(identifier)
        self.assertIsNotNone(result_notification)

    def test_get_notification_not_found(self):
        result_notification = self.service.get("unknown-identifier")
        self.assertIsNone(result_notification)

    def test_update_notification(self):
        identifier = f"{settings.SERVICE_NAME}_test-notification"
        self.created_identifiers.append(identifier)

        self.service.upsert(
            title="Test Notification",
            body="This is a test notification",
            scheduled_for=timezone.now() + timedelta(minutes=10),
            identifier=identifier,
            context={},
            device_ids=["device1", "device2"],
            notification_type="test",
            module_slug=settings.SERVICE_NAME,
        )

        new_scheduled_for = timezone.now() + timedelta(minutes=20)
        new_device_ids = ["device3", "device4"]
        self.service.upsert(
            title="Test Notification",
            body="This is a test notification",
            scheduled_for=new_scheduled_for,
            identifier=identifier,
            context={},
            device_ids=new_device_ids,
            notification_type="test",
            module_slug=settings.SERVICE_NAME,
        )
        updated_notification = self.service.get(identifier)
        device_ids = set(d.external_id for d in updated_notification.devices.all())
        self.assertEqual(
            device_ids,
            {"device1", "device2", "device3", "device4"},
        )

    def test_delete_notification(self):
        identifier = f"{settings.SERVICE_NAME}_test-notification"
        self.service.upsert(
            title="Test Notification",
            body="This is a test notification",
            scheduled_for=timezone.now() + timedelta(minutes=10),
            identifier=identifier,
            context={},
            device_ids=["device1", "device2"],
            notification_type="test",
            module_slug=settings.SERVICE_NAME,
        )

        self.service.delete(identifier)
        self.assertIsNone(self.service.get(identifier))
