import freezegun
from django.core.management import call_command
from model_bakery import baker

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from survey.models import Answer, SurveyVersion, SurveyVersionEntry


class TestCommand(ResponsesActivatedAPITestCase):
    def setUp(self):

        with freezegun.freeze_time("2024-06-01 12:00:00"):
            call_command("surveymockdata")
            survey_version = SurveyVersion.objects.first()
            email_question = survey_version.questions.filter(
                question_type="email"
            ).first()
            non_email_question = survey_version.questions.filter(
                question_type="text"
            ).first()
            entry = baker.make(SurveyVersionEntry, survey_version=survey_version)
            self.email_answer = baker.make(
                Answer,
                survey_version_entry=entry,
                question=email_question,
                answer="test@example.com",
            )
            self.text_answer = baker.make(
                Answer,
                survey_version_entry=entry,
                question=non_email_question,
                answer="This is a text answer.",
            )

    @freezegun.freeze_time("2024-08-01 12:00:00")
    def test_cleanup_email_addresses_within_timeframe(self):
        self.cleanup_email_addresses_base_case(expected_answer=self.email_answer.answer)

    @freezegun.freeze_time("2024-12-01 12:00:00")
    def test_cleanup_email_addresses_after_timeframe(self):
        self.cleanup_email_addresses_base_case(expected_answer="")

    def cleanup_email_addresses_base_case(self, expected_answer):
        # check that the number of answers and entries remains the same after cleanup
        count_answers_before_cleanup = Answer.objects.all().count()
        count_entries_before_cleanup = SurveyVersionEntry.objects.all().count()

        call_command("cleanupemailaddresses")

        count_answers_after_cleanup = Answer.objects.all().count()
        self.assertEqual(count_answers_after_cleanup, count_answers_before_cleanup)
        count_entries_after_cleanup = SurveyVersionEntry.objects.all().count()
        self.assertEqual(count_entries_after_cleanup, count_entries_before_cleanup)

        # check that email answers are as expected and non-email answers are not affected
        entry = SurveyVersionEntry.objects.first()
        for answer in entry.answers.all():
            if answer.question.question_type == "email":
                self.assertEqual(answer.answer, expected_answer)
            elif answer.question.question_type == "text":
                self.assertEqual(answer.answer, self.text_answer.answer)
