from datetime import timedelta

from django.conf import settings
from django.contrib import admin
from django.contrib.admin.widgets import BaseAdminDateWidget
from django.contrib.auth.models import Group, User
from django.test import RequestFactory, TestCase
from django.utils import timezone
from model_bakery import baker

from waste.admin.notification_admin import NotificationAdmin, NotificationAdminForm
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

    def test_send_at_uses_time_picker_on_time_subwidget(self):
        request = self.factory.get("/admin/waste/manualnotification/add/")
        request.user = self.user

        form_class = self.admin_instance.get_form(request)
        form = form_class()
        widget = form.fields["send_at"].widget

        self.assertIsInstance(widget.widgets[0], BaseAdminDateWidget)
        self.assertEqual(widget.widgets[1].input_type, "time")
        self.assertEqual(widget.widgets[1].format, "%H:%M")

    def test_destination_form_allows_no_destination_but_rejects_both(self):
        base_data = {
            "title": "Test",
            "message": "Keep this message",
            "created_by": self.user.pk,
        }
        deeplink = "amsterdam://afvalwijzer/GA"
        destination_error = "Vul óf een externe URL óf een deeplink in, niet beide."

        form = NotificationAdminForm(data={**base_data, "url": "", "deeplink": ""})
        self.assertTrue(form.is_valid(), form.errors)

        form = NotificationAdminForm(
            data={
                **base_data,
                "url": "https://example.com/path",
                "deeplink": deeplink,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(list(form.non_field_errors()), [destination_error])

    def test_destination_form_accepts_fixed_fraction_deeplink(self):
        form = NotificationAdminForm(
            data={
                "title": "Test",
                "message": "Keep this message",
                "created_by": self.user.pk,
                "url": "",
                "deeplink": "amsterdam://afvalwijzer/GA",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["message"], "Keep this message")
        self.assertEqual(form.cleaned_data["deeplink"], "amsterdam://afvalwijzer/GA")
        choices = list(form.fields["deeplink"].choices)
        self.assertEqual(choices[0][0], "")
        self.assertEqual(
            choices[1:],
            [
                (f"amsterdam://afvalwijzer/{code}", code)
                for code in (
                    "GA",
                    "GFT",
                    "Glas",
                    "Kerstbomen",
                    "Papier",
                    "Plastic",
                    "Rest",
                    "Textiel",
                )
            ],
        )

    def test_destination_form_accepts_external_url(self):
        form = NotificationAdminForm(
            data={
                "title": "Test",
                "message": "Keep this message",
                "created_by": self.user.pk,
                "url": "https://example.com/path",
                "deeplink": "",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["url"], "https://example.com/path")

    def test_destination_form_rejects_malformed_url(self):
        form = NotificationAdminForm(
            data={
                "title": "Test",
                "message": "Keep this message",
                "created_by": self.user.pk,
                "url": "not a URL",
                "deeplink": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("url", form.errors)

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
