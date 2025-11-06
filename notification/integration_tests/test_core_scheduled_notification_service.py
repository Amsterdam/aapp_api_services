import logging
from datetime import datetime, timedelta

import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APITestCase

from core.services.scheduled_notification import (
    NotificationServiceError,
    ScheduledNotificationService,
)

logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestCoreScheduledNotificationService(APITestCase):
    def setUp(self):
        self.service = ScheduledNotificationService()
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

    def test_add_notification_with_unknown_image_id(self):
        identifier = f"{settings.SERVICE_NAME}_test-notification"
        self.created_identifiers.append(identifier)
        unknown_image_id = 99999999

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
        )

        self.assertTrue(new_scheduled_notification)
        scheduled_expires_at = datetime.fromisoformat(
            new_scheduled_notification["expires_at"]
        )
        self.assertEqual(scheduled_expires_at.timestamp(), expires_at.timestamp())

    def test_get_notification(self):
        identifier = f"{settings.SERVICE_NAME}_test-notification"
        self.created_identifiers.append(identifier)

        new_notification = self.service.upsert(
            title="Test Notification",
            body="This is a test notification",
            scheduled_for=timezone.now() + timedelta(minutes=10),
            identifier=identifier,
            context={},
            device_ids=["device1", "device2"],
            notification_type="test",
        )

        result_notification = self.service.get(identifier)
        self.assertEqual(result_notification["title"], new_notification["title"])
        self.assertEqual(result_notification["body"], new_notification["body"])
        self.assertEqual(
            result_notification["scheduled_for"], new_notification["scheduled_for"]
        )
        self.assertEqual(result_notification["context"], new_notification["context"])
        self.assertEqual(
            result_notification["device_ids"], new_notification["device_ids"]
        )
        self.assertEqual(
            result_notification["notification_type"],
            new_notification["notification_type"],
        )

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
        )

        new_scheduled_for = timezone.now() + timedelta(minutes=20)
        new_device_ids = ["device3", "device4"]
        updated_notification = self.service.upsert(
            title="Test Notification",
            body="This is a test notification",
            scheduled_for=new_scheduled_for,
            identifier=identifier,
            context={},
            device_ids=new_device_ids,
            notification_type="test",
        )

        self.assertEqual(
            set(updated_notification["device_ids"]),
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
        )

        self.service.delete(identifier)
        self.assertIsNone(self.service.get(identifier))
