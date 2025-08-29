from adminsortable2.admin import SortableAdminBase
from django import forms
from django.contrib import admin
from django.contrib.admin import TabularInline

from contact.models.survey_models import Answer, SurveyVersionEntry


class SurveyVersionEntryAdmin(SortableAdminBase, admin.ModelAdmin):
    class SurveyVersionEntryAdminForm(forms.ModelForm):
        class Meta:
            model = SurveyVersionEntry
            fields = "__all__"

    class AnswerInLine(TabularInline):
        model = Answer
        fields = ["survey_version_entry", "question", "answer"]
        readonly_fields = ["survey_version_entry", "question", "answer"]
        extra = 0

    form = SurveyVersionEntryAdminForm
    list_display = ["id", "survey_version", "created_at"]
    readonly_fields = ["survey_version", "created_at"]
    inlines = [AnswerInLine]
    ordering = ["-id"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
