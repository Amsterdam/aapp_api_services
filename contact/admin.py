from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group, User

from .models import OpeningHours, OpeningHoursException

OPENING_TIME_WIDGET = {
    "opens_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
    "closes_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
}

admin.site.site_header = "Amsterdam App Admin"
admin.site.site_title = "Amsterdam App"
admin.site.index_title = "Openingstijden Admin"


class OpeningHoursAdmin(admin.ModelAdmin):
    class OpeningHoursAdminForm(forms.ModelForm):
        class Meta:
            model = OpeningHours
            fields = "__all__"
            widgets = OPENING_TIME_WIDGET

    form = OpeningHoursAdminForm
    list_display = ["city_office", "day_of_week", "formatted_opens", "formatted_closes"]
    readonly_fields = ("formatted_opens", "formatted_closes")

    def formatted_opens(self, obj):
        return obj.opens_time.strftime("%H:%M") if obj.opens_time else "-"

    def formatted_closes(self, obj):
        return obj.closes_time.strftime("%H:%M") if obj.closes_time else "-"

    formatted_opens.short_description = "Open"
    formatted_closes.short_description = "Sluit"


class OpeningHourExceptionsAdmin(admin.ModelAdmin):
    class OpeningHourExceptionsAdminForm(forms.ModelForm):
        class Meta:
            model = OpeningHoursException
            fields = "__all__"
            widgets = OPENING_TIME_WIDGET

    form = OpeningHourExceptionsAdminForm
    list_display = ["city_office", "date", "formatted_opens", "formatted_closes"]
    readonly_fields = ("formatted_opens", "formatted_closes")

    def formatted_opens(self, obj):
        return obj.opens_time.strftime("%H:%M") if obj.opens_time else "-"

    formatted_opens.short_description = "Open"

    def formatted_closes(self, obj):
        return obj.closes_time.strftime("%H:%M") if obj.closes_time else "-"

    formatted_closes.short_description = "Sluit"


admin.site.register(OpeningHours, OpeningHoursAdmin)
admin.site.register(OpeningHoursException, OpeningHourExceptionsAdmin)
admin.site.unregister(User)
admin.site.unregister(Group)
