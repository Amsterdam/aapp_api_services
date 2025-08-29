from datetime import timedelta

from django.core.management import BaseCommand
from django.utils import timezone

from contact.models.survey_models import (
    Choice,
    Condition,
    Question,
    Survey,
    SurveyVersion,
    SurveyVersionQuestion,
)
from contact.survey.named_tuples import ConditionType, QuestionType, TeamCode


class Command(BaseCommand):
    help = "Insert a mock survey into the database"

    def handle(self, *args, **options):
        survey, _ = Survey.objects.get_or_create(
            title="Klanttevredenheid Amsterdam App",
            unique_code="ams-app",
            team=TeamCode.AAPP,
        )
        survey_version_1 = survey.surveyversion_set.first()
        if not survey_version_1:
            survey_version_1 = SurveyVersion.objects.create(
                survey=survey,
                version=1,
                active_from=timezone.now() - timedelta(days=1),
            )

        q1 = Question.objects.create(
            question_text="Welk rapportcijfer geeft u vandaag aan de Amsterdam App?",
            question_type=QuestionType.RADIO.value,
            required=True,
            default="q1_10",
            sort_order=1,
        )
        choices = [
            Choice(label=str(i), text=str(i), sort_order=i, question=q1)
            for i in range(1, 11)
        ]
        Choice.objects.bulk_create(choices)

        q2 = Question.objects.create(
            question_text="Kunt u toelichten waarom u dit cijfer geeft?",
            question_type=QuestionType.TEXT.value,
            required=False,
            sort_order=2,
        )

        q3 = Question.objects.create(
            question_text="Wat was er niet goed aan de Amsterdam App?",
            question_type=QuestionType.CHECK.value,
            required=False,
            conditions_type="or",
            sort_order=3,
        )
        choices = [
            Choice(
                question=q3,
                label="onoverzichtelijk",
                text="Het is onoverzichtelijk",
                sort_order=1,
            ),
            Choice(question=q3, label="traag", text="De app is traag", sort_order=2),
            Choice(question=q3, label="crashte", text="De app crashte", sort_order=3),
            Choice(
                question=q3,
                label="foutmeldingen",
                text="Ik kreeg foutmeldingen",
                sort_order=4,
            ),
            Choice(
                question=q3,
                label="anders",
                text="Anders, namelijk:",
                sort_order=5,
                show_textfield=True,
            ),
        ]
        Choice.objects.bulk_create(choices)
        conditions = [
            Condition(
                question=q3,
                reference_question=q1,
                value=str(i),
                type=ConditionType.EQUAL.value,
            )
            for i in range(1, 7)
        ]
        Condition.objects.bulk_create(conditions)

        q4 = Question.objects.create(
            question_text="Wat is uw favoriete functie van de Amsterdam App?",
            question_type=QuestionType.SELECT.value,
            required=False,
            sort_order=4,
        )
        choices = [
            Choice(
                question=q4, label="afspraken", text="Afspraken maken", sort_order=1
            ),
            Choice(question=q4, label="meldingen", text="Meldingen doen", sort_order=2),
            Choice(
                question=q4, label="informatie", text="Informatie zoeken", sort_order=3
            ),
            Choice(question=q4, label="anders", text="Anders, namelijk:", sort_order=4),
        ]
        Choice.objects.bulk_create(choices)

        survey_version_questions = [
            SurveyVersionQuestion(
                survey_version=survey_version_1, question=q1, sort_order=1
            ),
            SurveyVersionQuestion(
                survey_version=survey_version_1, question=q2, sort_order=2
            ),
            SurveyVersionQuestion(
                survey_version=survey_version_1, question=q3, sort_order=3
            ),
            SurveyVersionQuestion(
                survey_version=survey_version_1, question=q4, sort_order=4
            ),
        ]
        SurveyVersionQuestion.objects.bulk_create(survey_version_questions)
