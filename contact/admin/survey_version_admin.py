from adminsortable2.admin import (
    SortableAdminBase,
    SortableTabularInline,
)
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.utils import timezone

from contact.models.survey_models import (
    SurveyVersion,
    SurveyVersionEntry,
    SurveyVersionQuestion,
)


class InlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in list(self.fields):
            w = self.fields[name].widget
            if isinstance(w, RelatedFieldWidgetWrapper):
                w.can_add_related = False
                w.can_change_related = False
                w.can_delete_related = False
                w.can_view_related = False


def survey_version_is_locked(survey_version):
    if not survey_version:
        return False
    if survey_version.active_from <= timezone.now():
        return True
    if SurveyVersionEntry.objects.filter(survey_version=survey_version).exists():
        return True
    return False


class SurveyVersionAdmin(SortableAdminBase, admin.ModelAdmin):
    class SurveyVersionAdminForm(forms.ModelForm):
        class Meta:
            model = SurveyVersion
            fields = "__all__"

    class QuestionInLine(SortableTabularInline):
        model = SurveyVersionQuestion
        form = InlineForm
        extra = 0

        def choices_count(self, obj):
            return obj.choice_set.count()

        choices_count.short_description = "Aantal keuzes"

        def conditional(self, obj):
            return obj.condition_set.exists()

        conditional.short_description = "Is conditioneel"

        def has_change_permission(self, request, obj=None):
            if obj and survey_version_is_locked(obj):
                return False
            return True

        def has_delete_permission(self, request, obj=None):
            if obj and survey_version_is_locked(obj):
                return False
            return True

        def has_add_permission(self, request, obj=None):
            if obj and survey_version_is_locked(obj):
                return False
            return True

    form = SurveyVersionAdminForm
    list_display = [
        "survey",
        "version",
        "active_from",
        "created_at",
        "survey__unique_code",
    ]
    readonly_fields = ["created_at"]
    inlines = [QuestionInLine]
    list_filter = ["survey", "questions"]

    def has_change_permission(self, request, obj=None):
        if obj and survey_version_is_locked(obj):
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        if obj and survey_version_is_locked(obj):
            return False
        return True
