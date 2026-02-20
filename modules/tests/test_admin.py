from datetime import timedelta

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.utils import timezone
from model_bakery import baker

from modules.admin.notification_admin import NotificationAdmin
from modules.models import Notification
from modules.services.notification import NotificationService
from notification.models import ScheduledNotification


class TestNotificationAdmin(TestCase):
    databases = {"default", "notification"}

    def setUp(self):
        self.user = baker.make(User, username="mockuser")
        self.notification_service = NotificationService()
        self.factory = RequestFactory()

    def test_delete_removes_scheduled_notification(self):
        # create timestamps
        created_at = timezone.now()
        send_at = created_at + timedelta(hours=2)

        # create notification that should match the scheduled identifier
        notif = baker.make(
            Notification, created_by=self.user, created_at=created_at, send_at=send_at
        )

        self.notification_service.upsert_scheduled_notification(notif)

        identifier = self.notification_service._create_identifier(
            created_at=created_at, created_by=self.user
        )

        # sanity check
        self.assertTrue(
            ScheduledNotification.objects.filter(identifier=identifier).exists()
        )

        # call admin delete
        admin_instance = NotificationAdmin(Notification, admin.site)
        request = self.factory.post(
            "/admin/modules/notification/{}/delete/".format(notif.pk)
        )
        request.user = self.user

        admin_instance.delete_model(request, notif)

        # scheduled notification should be deleted and the notification object removed
        self.assertFalse(
            ScheduledNotification.objects.filter(identifier=identifier).exists()
        )
        self.assertFalse(Notification.objects.filter(pk=notif.pk).exists())
