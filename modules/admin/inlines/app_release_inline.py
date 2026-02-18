from adminsortable2.admin import SortableTabularInline
from django import forms

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
        else:
            modules_not_in_release = Module.objects.exclude(
                moduleversion__apprelease=parent_release
            )
            qs = ModuleVersion.objects.filter(module__in=modules_not_in_release)
            self.fields["module_version"].queryset = qs


class ReleaseModuleStatusInline(SortableTabularInline, ModuleAdminMixin):
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

    def icon_svg(self, obj):
        return super().icon_svg(obj.module_version)

    def module_status(self, obj):
        return super().module_status(obj.module_version.module)

    def get_readonly_fields(self, request, obj=None):
        return ["icon_svg", "module_status"]

    def get_formset(self, request, obj=None, **kwargs):
        # ── 1) Prepare your “initial” list and decide how many extra forms
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

        # ── 2) Let Django build the formset class with that many extra forms
        FormSet = super().get_formset(request, obj, extra=extra_count, **kwargs)

        # ── 3) Subclass to inject the data after init
        class PrefilledFormSet(FormSet):
            def __init__(self, *args, **fs_kwargs):
                super().__init__(*args, **fs_kwargs)

                # Only prefill when unbound (first GET)
                if initial_data is not None and not self.is_bound:
                    for idx, form in enumerate(self.forms):
                        for name, val in initial_data[idx].items():
                            form.initial[name] = val
                            form.fields[name].initial = val

        # ── 4) Turn off the icons on the FK widgets
        for fld in PrefilledFormSet.form.base_fields.values():
            fld.widget.can_add_related = False
            fld.widget.can_change_related = False
            fld.widget.can_delete_related = False

        # ── 5) Wrap the form so that parent_release arrives in its __init__
        class BoundForm(FormSet.form):
            def __init__(self, *args, **kw):
                kw["parent_release"] = obj
                super().__init__(*args, **kw)

        PrefilledFormSet.form = BoundForm

        return PrefilledFormSet
