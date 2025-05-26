from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.db.models import Case, F, IntegerField, Value, When

from contact.models import (
    CityOfficeOpeningHours,
    OpeningHoursException,
    RegularOpeningHours,
    WeekDay,
)

OPENING_TIME_WIDGET = {
    "opens_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
    "closes_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
}

admin.site.site_header = "Amsterdam App Admin"
admin.site.site_title = "Amsterdam App"
admin.site.index_title = "Openingstijden Admin"


class OpeningHourExceptionsAdmin(admin.ModelAdmin):
    class OpeningHourExceptionsAdminForm(forms.ModelForm):
        class Meta:
            model = OpeningHoursException
            fields = "__all__"
            widgets = OPENING_TIME_WIDGET

    form = OpeningHourExceptionsAdminForm
    list_display = [
        "get_description",
        "get_date",
        "get_opening_status",
        "get_affected_offices",
    ]
    list_filter = ["date", "affected_offices"]
    search_fields = ["description", "affected_offices__title"]
    ordering = ["-date"]
    filter_horizontal = ["affected_offices"]
    readonly_fields = ("formatted_opens", "formatted_closes", "get_opening_status")

    def get_description(self, obj):
        if obj.description:
            return obj.description
        return obj.date.strftime("%d-%m-%Y")

    get_description.short_description = "Rede"

    def get_date(self, obj):
        return obj.date.strftime("%d-%m-%Y")

    get_date.short_description = "Datum"
    get_date.admin_order_field = "date"

    def get_opening_status(self, obj):
        if obj.opens_time is None and obj.closes_time is None:
            return "Gesloten"
        elif obj.opens_time and obj.closes_time:
            return f"{obj.opens_time.strftime('%H:%M')} - {obj.closes_time.strftime('%H:%M')}"
        return "-"

    get_opening_status.short_description = "Preview"

    def get_affected_offices(self, obj):
        return ", ".join([office.title for office in obj.affected_offices.all()])

    get_affected_offices.short_description = "Betrokken loketten"

    def formatted_opens(self, obj):
        return obj.opens_time.strftime("%H:%M") if obj.opens_time else "-"

    def formatted_closes(self, obj):
        return obj.closes_time.strftime("%H:%M") if obj.closes_time else "-"

    formatted_opens.short_description = "Open"
    formatted_closes.short_description = "Sluit"

    fieldsets = (
        (None, {"fields": ("description", "date", "affected_offices")}),
        (
            "Preview",
            {
                "fields": ("opens_time", "closes_time", "get_opening_status"),
                "description": "Laat beide velden leeg als het loket de hele dag gesloten is.",
            },
        ),
    )


class RegularOpeningHoursAdmin(admin.ModelAdmin):
    class RegularOpeningHoursAdminForm(forms.ModelForm):
        class Meta:
            model = RegularOpeningHours
            fields = "__all__"
            widgets = OPENING_TIME_WIDGET

    form = RegularOpeningHoursAdminForm


class RegularOpeningHoursInline(admin.TabularInline):
    model = RegularOpeningHours
    form = RegularOpeningHoursAdmin.RegularOpeningHoursAdminForm
    max_num = 7
    extra = 0
    can_delete = False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            custom_order=Case(
                When(day_of_week=0, then=Value(6)),  # Sunday last
                default=F("day_of_week") - 1,  # Monday=0, Tuesday=1, ..., Saturday=5
                output_field=IntegerField(),
            )
        ).order_by("custom_order")

    def has_add_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        """When created, makes day_of_week readonly"""
        if obj:
            return ["day_of_week"]
        return []

    def get_fields(self, request, obj=None):
        """Specify order of fields"""
        return ["day_of_week", "opens_time", "closes_time"]


class CityOfficeOpeningHoursAdmin(admin.ModelAdmin):
    week_days = WeekDay.names[1:] + WeekDay.names[:1]  # Move Sunday to the end
    list_display = ["city_office"] + [f"get_{day.lower()}" for day in week_days]
    search_fields = ["city_office__title"]
    list_filter = ["city_office"]
    inlines = [RegularOpeningHoursInline]
    ordering = ["city_office__order"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["city_office"]
        return []

    def create_hours_string(self, obj, WeekDay):
        regular_hours = obj.regularopeninghours_set.filter(day_of_week=WeekDay).first()
        if not regular_hours:
            return "-"
        if not regular_hours.opens_time or not regular_hours.closes_time:
            return "-"
        return f"{regular_hours.opens_time.strftime('%H:%M')} - {regular_hours.closes_time.strftime('%H:%M')}"

    def get_monday(self, obj):
        return self.create_hours_string(obj, WeekDay.MONDAY)

    get_monday.short_description = WeekDay.MONDAY.label

    def get_tuesday(self, obj):
        return self.create_hours_string(obj, WeekDay.TUESDAY)

    get_tuesday.short_description = WeekDay.TUESDAY.label

    def get_wednesday(self, obj):
        return self.create_hours_string(obj, WeekDay.WEDNESDAY)

    get_wednesday.short_description = WeekDay.WEDNESDAY.label

    def get_thursday(self, obj):
        return self.create_hours_string(obj, WeekDay.THURSDAY)

    get_thursday.short_description = WeekDay.THURSDAY.label

    def get_friday(self, obj):
        return self.create_hours_string(obj, WeekDay.FRIDAY)

    get_friday.short_description = WeekDay.FRIDAY.label

    def get_saturday(self, obj):
        return self.create_hours_string(obj, WeekDay.SATURDAY)

    get_saturday.short_description = WeekDay.SATURDAY.label

    def get_sunday(self, obj):
        return self.create_hours_string(obj, WeekDay.SUNDAY)

    get_sunday.short_description = WeekDay.SUNDAY.label


admin.site.register(CityOfficeOpeningHours, CityOfficeOpeningHoursAdmin)
admin.site.register(RegularOpeningHours, RegularOpeningHoursAdmin)
admin.site.register(OpeningHoursException, OpeningHourExceptionsAdmin)
admin.site.unregister(RegularOpeningHours)
admin.site.unregister(User)
admin.site.unregister(Group)
