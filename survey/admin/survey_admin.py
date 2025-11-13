from django import forms
from django.contrib import admin
from django.contrib.admin import TabularInline
from django.utils import timezone

from survey.admin.survey_version_admin import InlineForm
from survey.models import (
    Survey,
    SurveyConfiguration,
    SurveyVersion,
    SurveyVersionEntry,
)


def survey_is_locked(survey):
    survey_versions = SurveyVersion.objects.filter(survey=survey)
    for sv in survey_versions:
        if sv.active_from <= timezone.now():
            return True
        if SurveyVersionEntry.objects.filter(survey_version=sv).exists():
            return True
    return False


class SurveyAdmin(admin.ModelAdmin):
    class SurveyAdminForm(forms.ModelForm):
        class Meta:
            model = Survey
            fields = "__all__"

    class SurveyConfigInLine(TabularInline):
        model = SurveyConfiguration
        form = InlineForm
        extra = 0

        def has_delete_permission(self, request, obj=None):
            if obj and survey_is_locked(obj):
                return False
            return True

    form = SurveyAdminForm
    list_display = [
        "title",
        "unique_code",
        "team",
        "is_actief",
    ]
    inlines = [SurveyConfigInLine]
    list_filter = ["team"]

    def is_actief(self, obj) -> bool:
        return survey_is_locked(obj)

    def get_readonly_fields(self, request, obj=None):
        if obj and survey_is_locked(obj):
            return ["unique_code", "team"]
        return super().get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and survey_is_locked(obj):
            return False
        return True
