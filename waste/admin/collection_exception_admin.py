from django.contrib import admin
from django.utils.html import format_html

from waste.models import WasteCollectionException


class WasteCollectionExceptionAdmin(admin.ModelAdmin):
    model = WasteCollectionException

    @admin.display(description="Belangrijke informatie")
    def affected_routes_info(self, obj=None):
        return format_html(
            "<div class='help'><strong style='font-size: 1.2em; font-weight: 600; color: red;'>Als er in het onderstaande veld geen routes worden gekozen, worden <u>alle routes</u> beïnvloed door deze uitzondering.</strong></div>"
        )

    readonly_fields = ["affected_routes_info"]
    fields = ["date", "reason", "affected_routes_info", "affected_routes"]
    ordering = ["date"]
    list_display = ["date", "reason"]
    filter_horizontal = ["affected_routes"]
