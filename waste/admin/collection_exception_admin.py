from django.contrib import admin

from waste.models import WasteCollectionException


class WasteCollectionExceptionAdmin(admin.ModelAdmin):
    model = WasteCollectionException
    fields = ["date", "reason", "affected_routes"]
    ordering = ["date"]
    list_display = ["date", "reason"]
    filter_horizontal = ["affected_routes"]
