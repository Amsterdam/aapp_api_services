from django.contrib import admin

from waste.models import WasteCollectionException


class WasteCollectionExceptionAdmin(admin.ModelAdmin):
    model = WasteCollectionException
    fields = ["date", "reason"]
    ordering = ["date"]
    list_display = ["date", "reason"]
