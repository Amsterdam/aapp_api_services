from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from model_bakery import baker

from waste.admin.recycle_admin import (
    OpeningHoursExceptionAdmin,
    RegularOpeningHoursInline,
)
from waste.models import OpeningHoursException, RecycleLocationOpeningHours


class TestRecycleAdmin(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = baker.make(User, username="mockuser")

    def test_opening_hours_exception_uses_time_picker_widgets(self):
        admin_instance = OpeningHoursExceptionAdmin(OpeningHoursException, admin.site)
        request = self.factory.get("/admin/waste/openinghoursexception/add/")
        request.user = self.user

        form_class = admin_instance.get_form(request)

        self.assertEqual(
            form_class.base_fields["opens_time"].widget.input_type,
            "time",
        )
        self.assertEqual(
            form_class.base_fields["opens_time"].widget.format,
            "%H:%M",
        )
        self.assertEqual(
            form_class.base_fields["closes_time"].widget.input_type,
            "time",
        )
        self.assertEqual(
            form_class.base_fields["closes_time"].widget.format,
            "%H:%M",
        )

    def test_regular_opening_hours_inline_uses_time_picker_widgets(self):
        inline = RegularOpeningHoursInline(RecycleLocationOpeningHours, admin.site)
        request = self.factory.get("/admin/waste/recyclelocationopeninghours/")
        request.user = self.user

        formset = inline.get_formset(request)

        self.assertEqual(
            formset.form.base_fields["opens_time"].widget.input_type,
            "time",
        )
        self.assertEqual(
            formset.form.base_fields["opens_time"].widget.format,
            "%H:%M",
        )
        self.assertEqual(
            formset.form.base_fields["closes_time"].widget.input_type,
            "time",
        )
        self.assertEqual(
            formset.form.base_fields["closes_time"].widget.format,
            "%H:%M",
        )
