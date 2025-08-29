from adminsortable2.admin import SortableAdminBase, SortableTabularInline
from django import forms
from django.contrib import admin
from django.contrib.admin import TabularInline
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.utils import timezone

from contact.admin.survey_version_admin import InlineForm
from contact.models.survey_models import Choice, Condition, Question, SurveyVersionEntry


def question_is_locked(question):
    if not question:
        return False
    survey_versions = question.survey_versions
    for sv in survey_versions.all():
        if sv.active_from <= timezone.now():
            return True
        if SurveyVersionEntry.objects.filter(survey_version=sv).exists():
            return True
    return False


class QuestionAdmin(SortableAdminBase, admin.ModelAdmin):
    class QuestionAdminForm(forms.ModelForm):
        class Meta:
            model = Question
            fields = "__all__"

    class ChoiceInLine(SortableTabularInline):
        model = Choice
        fields = ["id", "text", "label", "show_textfield"]
        readonly_fields = ["id"]
        extra = 0

        def has_change_permission(self, request, obj=None):
            if obj and question_is_locked(obj):
                return False
            return True

        def has_delete_permission(self, request, obj=None):
            if obj and question_is_locked(obj):
                return False
            return True

        def has_add_permission(self, request, obj=None):
            if obj and question_is_locked(obj):
                return False
            return True

    class ConditionInLine(TabularInline):
        model = Condition
        fields = ["reference_question", "type", "value"]
        fk_name = "question"
        extra = 0
        form = InlineForm

        def formfield_for_foreignkey(self, db_field, request, **kwargs):
            formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)

            def strip_icons(widget):
                if isinstance(widget, RelatedFieldWidgetWrapper):
                    widget.can_add_related = False
                    widget.can_change_related = False
                    widget.can_delete_related = False
                    widget.can_view_related = False

            strip_icons(formfield.widget)
            return formfield

    form = QuestionAdminForm
    list_display = ["question_id", "question_text", "question_type", "required"]
    readonly_fields = ["question_id"]
    fields = [
        "question_text",
        "description",
        "question_type",
        "required",
        "default",
        "orientation",
        "min_characters",
        "max_characters",
        "conditions_type",
    ]
    exclude = ["id", "sort_order", "question_id"]
    inlines = [ChoiceInLine, ConditionInLine]
    ordering = ["-id"]
    list_filter = ["survey_versions"]

    def question_id(self, obj):
        return obj.id

    def has_change_permission(self, request, obj=None):
        if obj and question_is_locked(obj):
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        if obj and question_is_locked(obj):
            return False
        return True
