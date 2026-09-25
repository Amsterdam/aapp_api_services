from django import forms
from django.forms.models import BaseInlineFormSet
from django.utils.safestring import mark_safe


class SortableInlineFormSet(BaseInlineFormSet):
    """Normalize inline order server-side before save."""

    sortable_field_name = "sort_order"

    def add_fields(self, form, index):
        super().add_fields(form, index)
        sort_field = self.sortable_field_name
        if sort_field in form.fields:
            form.fields[sort_field].required = False

    def _active_forms(self):
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if self.can_delete and self._should_delete_form(form):
                continue
            if not form.cleaned_data:
                continue
            if form.instance.pk is None and not form.has_changed():
                continue
            yield form

    def save(self, commit=True):
        sort_field = self.sortable_field_name
        active_forms = list(self._active_forms())

        def _submitted_sort_value(form):
            value = form.cleaned_data.get(sort_field)
            if value in (None, ""):
                return 10**9
            return int(value)

        active_forms.sort(key=_submitted_sort_value)

        for index, form in enumerate(active_forms, start=1):
            form.cleaned_data[sort_field] = index
            setattr(form.instance, sort_field, index)

        saved_instances = super().save(commit=commit)

        # Existing inline rows may not be considered "changed" by Django when only
        # ordering changed in the DOM. Persist normalized sort values explicitly.
        if commit:
            for index, form in enumerate(active_forms, start=1):
                instance = form.instance
                if instance.pk is None:
                    continue
                setattr(instance, sort_field, index)
                instance.save(update_fields=[sort_field])

        return saved_instances


class SortableInlineMixin:
    template = "admin/edit_inline/tabular_sortable.html"
    sortable_field_name = "sort_order"
    sortable_handle_field = "drag_handle"
    formset = SortableInlineFormSet

    class Media:
        js = ("js/admin_inline_sortable.js",)
        css = {"all": ("css/admin_inline_sortable.css",)}

    @staticmethod
    def drag_handle(_obj):
        return mark_safe(
            '<span class="js-sortable-handle" title="Versleep om te sorteren" '
            'aria-label="Versleep om te sorteren">&#x2630;</span>'
        )

    drag_handle.short_description = ""

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.order_by(self.sortable_field_name, "pk")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.sortable_field_name = self.sortable_field_name
        return formset

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if self.sortable_handle_field in fields:
            fields.remove(self.sortable_handle_field)
        fields.insert(0, self.sortable_handle_field)
        if self.sortable_field_name not in fields:
            fields.append(self.sortable_field_name)
        return fields

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if self.sortable_handle_field not in readonly_fields:
            readonly_fields.insert(0, self.sortable_handle_field)
        return readonly_fields

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == self.sortable_field_name:
            kwargs["widget"] = forms.HiddenInput()
        return super().formfield_for_dbfield(db_field, request, **kwargs)
