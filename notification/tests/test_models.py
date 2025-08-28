from django.db import IntegrityError
from django.test import TestCase
from model_bakery import baker

from notification.models import (
    Device,
    NotificationPushModuleDisabled,
    NotificationPushTypeDisabled,
)


class TestNotificationPushTypeDisabled(TestCase):
    def test_unique_together(self):
        device = baker.make(Device)
        notification_type = "test-notification-type"
        NotificationPushTypeDisabled.objects.create(
            device=device,
            notification_type=notification_type,
        )
        with self.assertRaises(IntegrityError):
            NotificationPushTypeDisabled.objects.create(
                device=device,
                notification_type=notification_type,
            )


class TestNotificationPushModuleDisabled(TestCase):
    def test_unique_together(self):
        device = baker.make(Device)
        module_slug = "test-module-slug"
        NotificationPushModuleDisabled.objects.create(
            device=device,
            module_slug=module_slug,
        )
        with self.assertRaises(IntegrityError):
            NotificationPushModuleDisabled.objects.create(
                device=device,
                module_slug=module_slug,
            )
