from django import forms
from django.contrib import admin

from core.admin.sortable import SortableInlineMixin
from modules.admin.admin_mixin import ModuleAdminMixin
from modules.models import Module, ModuleVersion, ReleaseModuleStatus


class ReleaseModuleStatusForm(forms.ModelForm):
    module_version = forms.ModelChoiceField(
        queryset=ModuleVersion.objects.all(),
        empty_label=None,
    )

    class Meta:
        model = ReleaseModuleStatus
        fields = "__all__"
        widgets = {
            "app_reason": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "fallback_url": forms.URLInput(
                attrs={
                    "size": 40,  # small-ish input
                    "placeholder": "https://…",
                }
            ),
        }

    def __init__(self, *args, parent_release=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            parent_module = self.instance.module_version.module
            qs = ModuleVersion.objects.filter(module=parent_module)
            self.fields["module_version"].queryset = qs
        elif parent_release is None:
            qs = ModuleVersion.objects.all()
        else:
            used_modules = Module.objects.exclude(
                moduleversion__apprelease=parent_release
            )
            qs = ModuleVersion.objects.filter(module__in=used_modules)
        self.fields["module_version"].queryset = qs.distinct()


class ReleaseModuleStatusInline(
    SortableInlineMixin, admin.TabularInline, ModuleAdminMixin
):
    model = ReleaseModuleStatus
    form = ReleaseModuleStatusForm
    fields = [
        "icon_svg",
        "module_version",
        "module_status",
        "status",
        "note",
        "app_reason",
        "fallback_url",
        "button_label",
    ]
    extra = 0
    extra_readonly_fields = ("icon_svg", "module_status")

    def icon_svg(self, obj):
        return super().icon_svg(obj.module_version)

    def module_status(self, obj):
        return super().module_status(obj.module_version.module)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        for field_name in self.extra_readonly_fields:
            if field_name not in readonly_fields:
                readonly_fields.append(field_name)
        return readonly_fields

    def get_formset(self, request, obj=None, **kwargs):
        # Prepare initial values and decide how many extra forms are needed.
        initial_data = None
        extra_count = self.extra
        if obj is None:
            release_id = request.GET.get("release") or request.POST.get("release")
            if release_id:
                qs = ReleaseModuleStatus.objects.filter(
                    app_release_id=release_id
                ).order_by("sort_order")
                initial_data = [
                    {
                        "module_version": r.module_version,
                        "status": r.status,
                        "note": r.note,
                        "app_reason": r.app_reason,
                        "fallback_url": r.fallback_url,
                    }
                    for r in qs
                ]
                extra_count = max(1, len(initial_data))

        # Let Django build the formset class with the computed extra forms.
        FormSet = super().get_formset(request, obj, extra=extra_count, **kwargs)

        # Subclass to inject initial values after the formset initializes.
        class PrefilledFormSet(FormSet):
            def __init__(self, *args, **fs_kwargs):
                super().__init__(*args, **fs_kwargs)

                # Only prefill when unbound (first GET).
                if initial_data is not None and not self.is_bound:
                    for idx, form in enumerate(self.forms):
                        if idx >= len(initial_data):
                            break
                        for name, val in initial_data[idx].items():
                            form.initial[name] = val
                            form.fields[name].initial = val

        # Turn off relation-action icons on FK widgets in inline forms.
        for fld in PrefilledFormSet.form.base_fields.values():
            fld.widget.can_add_related = False
            fld.widget.can_change_related = False
            fld.widget.can_delete_related = False

        # Wrap the form so parent_release reaches ReleaseModuleStatusForm.__init__.
        class BoundForm(FormSet.form):
            def __init__(self, *args, **kw):
                kw["parent_release"] = obj
                super().__init__(*args, **kw)

        PrefilledFormSet.form = BoundForm

        return PrefilledFormSet
