from datetime import timedelta

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.test import RequestFactory, TestCase
from django.utils import timezone
from model_bakery import baker

from waste.admin.notification_admin import DEADLINE_BUFFER_MINUTES, NotificationAdmin
from waste.models import ManualNotification
from waste.services.notification import ManualNotificationService


class TestNotificationAdmin(TestCase):
    databases = {"default", "notification"}

    def setUp(self):
        self.user = baker.make(User, username="mockuser")
        group = Group.objects.create(
            name=f"{settings.ENVIRONMENT_SLUG}-waste-notification-publisher"
        )
        self.user.groups.add(group)
        self.factory = RequestFactory()
        self.admin_instance = NotificationAdmin(ManualNotification, admin.site)
        self.notification_service = ManualNotificationService()

    def test_get_exclude_keeps_send_at_available_on_add(self):
        exclude = self.admin_instance.get_exclude(request=None)

        self.assertNotIn("send_at", exclude)
        self.assertIn("created_by", exclude)

    def test_delete_removes_scheduled_notification(self):
        notification = baker.make(
            ManualNotification,
            created_by=self.user,
            send_at=timezone.now() + timedelta(hours=2),
        )
        self.notification_service.send(notification)
        identifier = self.notification_service._create_identifier(notification.id)

        request = self.factory.post(
            f"/admin/waste/manualnotification/{notification.pk}/delete/"
        )
        request.user = self.user

        self.admin_instance.delete_model(request, notification)

        self.assertFalse(
            self.notification_service.get_scheduled_notification(identifier)
        )
        self.assertFalse(ManualNotification.objects.filter(pk=notification.pk).exists())

    def test_has_delete_permission_returns_false_within_deadline_buffer(self):
        notification = baker.make(
            ManualNotification,
            created_by=self.user,
            send_at=timezone.now() + timedelta(minutes=DEADLINE_BUFFER_MINUTES - 1),
        )
        request = self.factory.get(
            f"/admin/waste/manualnotification/{notification.pk}/change/"
        )
        request.user = self.user

        has_permission = self.admin_instance.has_delete_permission(
            request, notification
        )

        self.assertFalse(has_permission)
