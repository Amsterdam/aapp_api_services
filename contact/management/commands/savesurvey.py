from django.core.management import BaseCommand
from django.db import transaction

from contact.models.survey_models import (
    Choice,
    Condition,
    Question,
    Survey,
    SurveyVersion,
)
from contact.survey.definition import survey, survey_version_1
from contact.survey.named_tuples import QuestionType


class Command(BaseCommand):
    help = "Insert the survey into the database"

    def handle(self, *args, **options):
        questions, conditions, choices = [], [], []

        survey_obj = Survey(
            title=survey.title,
            unique_code=survey.unique_code,
            team=survey.team,
        )

        survey_version_obj = SurveyVersion(
            survey=survey_obj,
            version=survey_version_1.version,
            active_from=survey_version_1.active_from,
        )

        for q in survey_version_1.questions:
            if q.question_type == QuestionType.TEXT.value:
                new_question = Question(
                    id=q.question_id,
                    question_text=q.question_text,
                    required=q.required,
                    min_characters=q.min_characters,
                    max_characters=q.max_characters,
                    default=q.default,
                    description=q.description,
                    question_type=q.question_type,
                    conditions_type=q.conditions_type,
                    survey_version=survey_version_obj,
                )
                conditions += self.get_conditions(q)
                questions.append(new_question)
            elif q.question_type != QuestionType.TEXT.value:
                new_question = Question(
                    id=q.question_id,
                    question_text=q.question_text,
                    required=q.required,
                    question_type=q.question_type,
                    default=q.default,
                    description=q.description,
                    conditions_type=q.conditions_type,
                    survey_version=survey_version_obj,
                    orientation=q.orientation,
                )
                conditions += self.get_conditions(q)
                choices += self.get_choices(q)
                questions.append(new_question)

        with transaction.atomic():
            # Save the survey to the database
            survey_obj.save()
            survey_version_obj.save()
            [q.save() for q in questions]
            [c.save() for c in conditions]
            [c.save() for c in choices]

    def get_conditions(self, q):
        new_conditions = []
        for condition in q.conditions:
            new_condition = Condition(
                question_id=q.question_id,
                value=condition.value,
                type=condition.type,
                reference_question_id=condition.question_id,
            )
            new_conditions.append(new_condition)
        return new_conditions

    def get_choices(self, q):
        new_choices = []
        for choice in q.choices:
            new_choice = Choice(
                question_id=q.question_id,
                id=choice.id,
                text=choice.text,
                label=choice.label,
                show_textfield=choice.show_textfield,
            )
            new_choices.append(new_choice)
        return new_choices
