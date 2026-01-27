from django.contrib import admin
from django.db.models import Case, F, IntegerField, Value, When

from waste.models import RecycleLocationOpeningHours, RegularOpeningHours, WeekDay


class RegularOpeningHoursInline(admin.TabularInline):
    model = RegularOpeningHours
    max_num = 7
    extra = 0
    fields = ["day_of_week", "opens_time", "closes_time"]
    verbose_name = "Openingstijd"
    verbose_name_plural = "Openingstijden"
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

    def get_fields(self, request, obj=None):
        """Specify order of fields"""
        return ["day_of_week", "opens_time", "closes_time"]


class RecycleLocationOpeningHoursAdmin(admin.ModelAdmin):
    week_days = WeekDay.names[1:] + WeekDay.names[:1]
    inlines = [RegularOpeningHoursInline]
    list_display = ["recycle_location"] + [f"get_{day.lower()}" for day in week_days]
    list_filter = ["recycle_location"]
    ordering = ["recycle_location__name"]

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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not obj.regularopeninghours_set.exists():
            for day in WeekDay:
                RegularOpeningHours.objects.create(
                    recycle_location_opening_hours=obj, day_of_week=day.value
                )


class RecycleLocationOpeningHoursInline(admin.StackedInline):
    model = RecycleLocationOpeningHours
    extra = 0
    max_num = 1
    verbose_name = "Openingstijden"
    verbose_name_plural = "Openingstijden"


class RecycleLocationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "city",
        "city_district",
        "street",
        "number",
        "addition_letter",
        "addition_number",
        "postal_code",
        "latitude",
        "longitude",
        "commercial_waste",
    ]
    inlines = [RecycleLocationOpeningHoursInline]


class OpeningHoursExceptionAdmin(admin.ModelAdmin):
    list_display = [
        "get_description",
        "get_date",
        "get_opening_status",
        "get_affected_locations",
    ]
    list_filter = ["date", "affected_locations"]
    ordering = ["-date"]
    filter_horizontal = ["affected_locations"]
    readonly_fields = ["formatted_opens", "formatted_closes", "get_opening_status"]

    def get_description(self, obj):
        if obj.description:
            return obj.description
        return obj.date.strftime("%d-%m-%Y")

    get_description.short_description = "Reden"

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

    def get_affected_locations(self, obj):
        return ", ".join([location.name for location in obj.affected_locations.all()])

    get_affected_locations.short_description = "Betrokken locaties"

    def formatted_opens(self, obj):
        return obj.opens_time.strftime("%H:%M") if obj.opens_time else "-"

    def formatted_closes(self, obj):
        return obj.closes_time.strftime("%H:%M") if obj.closes_time else "-"

    formatted_opens.short_description = "Open"
    formatted_closes.short_description = "Sluit"

    fieldsets = (
        (None, {"fields": ("description", "date", "affected_locations")}),
        (
            "Preview",
            {
                "fields": ("opens_time", "closes_time", "get_opening_status"),
                "description": "Laat beide velden leeg als de locatie de hele dag gesloten is.",
            },
        ),
    )
