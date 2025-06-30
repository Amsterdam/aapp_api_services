from django import forms
from django.contrib.admin import TabularInline

from modules.admin.admin_mixin import ModuleAdminMixin
from modules.admin.utils import bump_major, bump_minor, bump_patch
from modules.models import AppRelease, ModuleVersion


class ModuleVersionForm(forms.ModelForm):
    version = forms.ChoiceField()

    class Meta:
        model = ModuleVersion
        fields = "__all__"
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2, "cols": 40}),
        }

    def __init__(self, *args, parent_module=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["version"].disabled = True

        last_version = self.instance.version
        opts = []
        if last_version:
            opts += [last_version]
        elif parent_module:
            last_module_version = parent_module.moduleversion_set.order_by(
                "-version"
            ).first()
            if last_module_version:
                last_version = last_module_version.version
            else:
                last_version = "0.0.0"
        else:
            last_version = "0.0.0"
        opts += [
            bump_patch(last_version),
            bump_minor(last_version),
            bump_major(last_version),
        ]
        self.fields["version"].choices = [(v, v) for v in opts]


class ModuleVersionInline(TabularInline, ModuleAdminMixin):
    model = ModuleVersion
    form = ModuleVersionForm
    fields = [
        "icon_svg",
        "title",
        "version",
        "icon",
        "description",
        "laatste_app_release",
        "created",
        "modified",
    ]
    readonly_fields = [
        "icon_svg",
        "laatste_app_release",
        "created",
        "modified",
    ]
    ordering = ["-created__date", "-version"]
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        Formset = super().get_formset(request, obj, **kwargs)
        parent = obj

        # wrap the form so that parent_module arrives in its __init__
        class BoundForm(Formset.form):
            def __init__(self, *args, **kw):
                kw["parent_module"] = parent
                super().__init__(*args, **kw)

        Formset.form = BoundForm
        return Formset

    def laatste_app_release(self, obj):
        """
        Returns the highest release version for the module.
        """
        return AppRelease.objects.filter(modules=obj).order_by("created").last()
