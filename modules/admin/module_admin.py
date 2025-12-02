from django.contrib import admin
from django.db import models

from modules.admin.admin_mixin import ModuleAdminMixin
from modules.admin.inlines.module_admin_inline import ModuleVersionInline
from modules.models import AppRelease


class ModuleAdmin(admin.ModelAdmin, ModuleAdminMixin):
    list_display = [
        "slug",
        "laatste_versie_naam",
        "laatste_icoon",
        "module_status",
        "note",
        "aantal_versies",
        "laatste_app_release",
    ]
    fields = [
        "slug",
        "status",
        "note",
        "app_reason",
        "fallback_url",
        "button_label",
    ]
    inlines = [ModuleVersionInline]
    actions = None

    class Media:
        js = ("js/persist_scroll.js",)

    def get_queryset(self, request):
        # Order by modified date of the latest version
        return (
            super()
            .get_queryset(request)
            .annotate(latest_version_modified=models.Max("moduleversion__modified"))
            .order_by("-latest_version_modified")
        )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["slug"]
        return super().get_readonly_fields(request, obj)

    def latest_version(self, obj):
        return obj.moduleversion_set.order_by("-version").first()

    def laatste_versie_naam(self, obj):
        version = self.latest_version(obj)
        if not version:
            return ""
        return f"{version.title} ({version.version})"

    def laatste_icoon(self, obj):
        version = self.latest_version(obj)
        if not version or not version.icon:
            return ""

        return self.icon_svg(version)

    def aantal_versies(self, obj):
        return obj.moduleversion_set.count()

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        context["show_save"] = False
        context["show_save_and_continue"] = True
        context["show_save_and_add_another"] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

    def laatste_app_release(self, obj):
        """
        Returns the highest release version for the module.
        """
        return AppRelease.objects.filter(modules__module=obj).order_by("created").last()
