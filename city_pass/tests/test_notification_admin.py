from django.contrib import admin
from django.contrib.admin.widgets import BaseAdminDateWidget
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from model_bakery import baker

from city_pass.admin.notification_admin import NotificationAdmin
from city_pass.models import Notification


class TestNotificationAdmin(TestCase):
    def setUp(self):
        self.user = baker.make(User, username="mockuser")
        self.factory = RequestFactory()

    def test_send_at_uses_time_picker_on_time_subwidget(self):
        admin_instance = NotificationAdmin(Notification, admin.site)
        request = self.factory.get("/admin/city_pass/notification/add/")
        request.user = self.user

        form_class = admin_instance.get_form(request)
        form = form_class()
        widget = form.fields["send_at"].widget

        self.assertIsInstance(widget.widgets[0], BaseAdminDateWidget)
        self.assertEqual(widget.widgets[1].input_type, "time")
        self.assertEqual(widget.widgets[1].format, "%H:%M")
