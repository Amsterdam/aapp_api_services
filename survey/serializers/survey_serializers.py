from django.db import transaction
from rest_framework import serializers

from survey.models import (
    Answer,
    Choice,
    Condition,
    Question,
    Survey,
    SurveyConfiguration,
    SurveyVersion,
    SurveyVersionEntry,
)


class SurveyVersionSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = SurveyVersion
        exclude = ["id", "survey"]

    def get_question_count(self, obj) -> int:
        return obj.questions.count()


class ConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Condition
        exclude = ["id", "question"]


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        exclude = ["id", "question", "sort_order"]


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)
    conditions = ConditionSerializer(many=True)

    class Meta:
        model = Question
        exclude = ["sort_order", "survey_versions"]


class SurveyVersionDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = SurveyVersion
        exclude = ["id", "survey"]


class SurveySerializer(serializers.ModelSerializer):
    latest_version = serializers.SerializerMethodField()

    def get_latest_version(self, obj) -> str:
        latest_version = obj.surveyversion_set.order_by("-version").first()
        return (
            SurveyVersionDetailSerializer(latest_version).data
            if latest_version
            else None
        )

    class Meta:
        model = Survey
        exclude = ["id"]


class SurveyConfigResponseSerializer(serializers.ModelSerializer):
    survey = SurveySerializer()

    class Meta:
        model = SurveyConfiguration
        fields = "__all__"


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["question", "answer"]


class SurveyVersionEntrySerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = SurveyVersionEntry
        exclude = ["id", "survey_version", "created_at"]

    @transaction.atomic
    def create(self, validated_data):
        answers = validated_data.pop("answers", [])
        entry = SurveyVersionEntry.objects.create(**validated_data)
        Answer.objects.bulk_create(
            [Answer(survey_version_entry=entry, **a) for a in answers]
        )
        return entry


class SurveyVersionEntryListSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)
    survey_unique_code = serializers.SerializerMethodField()

    class Meta:
        model = SurveyVersionEntry
        fields = "__all__"

    def get_survey_unique_code(self, obj) -> str:
        return obj.survey_version.survey.unique_code
