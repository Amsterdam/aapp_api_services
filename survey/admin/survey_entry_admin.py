from adminsortable2.admin import SortableAdminBase
from django import forms
from django.contrib import admin
from django.contrib.admin import TabularInline
from django.utils.html import format_html_join

from survey.models import Answer, SurveyVersionEntry


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
    list_display = ["id", "survey_version", "created_at", "antwoorden"]
    readonly_fields = ["survey_version", "created_at"]
    list_filter = ["survey_version__survey__team", "survey_version", "entry_point"]
    inlines = [AnswerInLine]
    ordering = ["-id"]

    def get_queryset(self, request):
        return SurveyVersionEntry.objects.prefetch_related("answers").select_related(
            "survey_version__survey"
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def antwoorden(self, obj):
        return format_html_join(
            "\n",
            "<li>{}: {}</li>",
            ((a.question.id, a.answer) for a in obj.answers.all()),
        )
