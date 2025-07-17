from adminsortable2.admin import (
    SortableAdminBase,
)
from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils import timezone

from modules.admin.forms.app_release_form import AppReleaseForm
from modules.admin.inlines.app_release_inline import ReleaseModuleStatusInline
from modules.models import AppRelease, Module, ReleaseModuleStatus


class AppReleaseAdmin(SortableAdminBase, admin.ModelAdmin):
    form = AppReleaseForm
    list_display = [
        "version",
        "status",
        "inactieve_modules",
        "inactieve_release_versies",
        "created",
    ]
    inlines = [ReleaseModuleStatusInline]
    actions = None
    ordering = ["-created__date", "-version"]
    readonly_fields = ["modules_not_included"]

    class Media:
        js = ("js/persist_scroll.js",)

    def get_fields(self, request, obj=None):
        fields = [
            "release",
            "release_notes",
            "published",
            "unpublished",
            "deprecated",
            "version",
            "modules_not_included",
        ]
        if not obj:
            fields += ["version_choice"]
        return fields

    def modules_not_included(self, obj):
        """Returns a list of versions not included in the current release."""
        return " | ".join(
            [str(m) for m in Module.objects.exclude(moduleversion__apprelease=obj)]
        )

    def add_view(self, request, form_url="", extra_context=None):
        class ReleaseSelectForm(forms.Form):
            release = forms.ModelChoiceField(
                AppRelease.objects.all().order_by("-created"), label="Release"
            )

        if "release" not in request.GET:
            if request.method == "POST":
                release_id = request.POST.get("release")
                if release_id:
                    return HttpResponseRedirect(f"{request.path}?release={release_id}")
            ctx = {
                **self.admin_site.each_context(request),
                "title": "Select latest release or release for hotfix",
                "form": ReleaseSelectForm(request.POST or None),
            }
            return TemplateResponse(request, "admin/modules/data_select.html", ctx)

        release_id = request.GET["release"]
        form_url = f"?release={release_id}"
        return super().add_view(request, form_url, extra_context)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        release_id = request.GET.get("release") or request.POST.get("release")
        if release_id:
            release = AppRelease.objects.get(pk=release_id)
            if release:
                initial.update(
                    version=release.version,
                    release_notes=release.release_notes,
                )
            initial["release"] = release_id
        return initial

    def status(self, obj):
        states = ["Supported"]
        today = timezone.now()
        if obj.unpublished and obj.unpublished <= today:
            return ""
        if not obj.published or obj.published >= today:
            states.append("pre-release")
        if obj.deprecated and obj.deprecated <= today:
            states.append("deprecated")
        return ", ".join(states)

    def inactieve_modules(self, obj):
        """Return a comma-separated list of inactive modules."""
        version_ids = obj.releasemodulestatus_set.values_list(
            "module_version", flat=True
        )
        qs = Module.objects.filter(
            status=Module.Status.INACTIVE, moduleversion__in=version_ids
        ).distinct()
        return ", ".join(str(m.slug) for m in qs)

    def inactieve_release_versies(self, obj):
        """Return a comma seperated list of inactive modules."""
        inactive_modules = obj.releasemodulestatus_set.filter(
            status=ReleaseModuleStatus.Status.INACTIVE
        )
        return ", ".join([str(r.module_version) for r in inactive_modules])

    def changelist_view(self, request, extra_context=None):
        messages.info(
            request,
            "⚠️ Wijzigingen zijn zichtbaar in de app na 60 seconden, vanwege caching.",
        )
        return super().changelist_view(request, extra_context)

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        context["show_save"] = False
        context["show_save_and_continue"] = True
        context["show_save_and_add_another"] = False
        return super().render_change_form(request, context, add, change, form_url, obj)
