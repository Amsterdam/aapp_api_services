from django.contrib import admin

from waste.models import WasteCollectionException


class WasteCollectionExceptionAdmin(admin.ModelAdmin):
    model = WasteCollectionException
    fields = ["date", "reason", "affected_routes"]
    ordering = ["date"]
    list_display = ["date", "reason"]
    filter_horizontal = ["affected_routes"]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # make sure the affected routes are ordered alphabetically in the admin form
        if db_field.name == "affected_routes":
            queryset = kwargs.get("queryset") or db_field.remote_field.model.objects
            kwargs["queryset"] = queryset.order_by("name")
        return super().formfield_for_manytomany(db_field, request, **kwargs)
