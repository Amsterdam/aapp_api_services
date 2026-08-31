from datetime import timedelta

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.test import RequestFactory, TestCase
from django.utils import timezone
from model_bakery import baker

from notification.models.waste_guide_models import WasteDevice
from waste.admin.notification_admin import NotificationAdmin
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

    def test_postal_area_field_is_populated_with_select_choices(self):
        baker.make(WasteDevice, device_id="device-a", postal_area="1011")
        baker.make(WasteDevice, device_id="device-b", postal_area="1012")

        form_class = self.admin_instance.get_form(request=self.factory.get("/admin/"))
        field = form_class.base_fields["postal_area"]

        self.assertEqual(field.__class__.__name__, "ChoiceField")
        self.assertIn(("1011", "1011"), field.choices)
        self.assertIn(("1012", "1012"), field.choices)
