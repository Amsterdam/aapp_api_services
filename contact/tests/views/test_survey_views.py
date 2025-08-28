import copy

from django.core.management import call_command
from django.urls import reverse

from contact.models.survey_models import Question
from core.tests.test_authentication import BasicAPITestCase


class AbstractSurveyTestCase(BasicAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("surveymockdata")


class TestSurveyView(AbstractSurveyTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("contact-surveys")

    def test_get_surveys_successfully(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)


class TestSurveyVersionView(AbstractSurveyTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("contact-survey-versions", kwargs={"unique_code": "ams-app"})

    def test_get_survey_versions_successfully(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)

    def test_unique_code_not_found(self):
        url = reverse("contact-survey-versions", kwargs={"unique_code": "foobar"})
        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 404)


class TestSurveyVersionDetailView(AbstractSurveyTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "contact-survey-version-detail",
            kwargs={"unique_code": "ams-app", "version": "1"},
        )

    def test_get_survey_version_detail_successfully(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data["version"], 1)

    def test_unique_code_not_found(self):
        url = reverse(
            "contact-survey-version-detail",
            kwargs={"unique_code": "foobar", "version": "1"},
        )
        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 404)

    def test_version_not_found(self):
        url = reverse(
            "contact-survey-version-detail",
            kwargs={"unique_code": "ams-app", "version": "99"},
        )
        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 404)


class TestSurveyVersionLatestView(AbstractSurveyTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "contact-survey-version-latest", kwargs={"unique_code": "ams-app"}
        )

    def test_get_survey_version_latest_successfully(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data["version"], 1)

    def test_unique_code_not_found(self):
        url = reverse("contact-survey-version-latest", kwargs={"unique_code": "foobar"})
        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 404)


class TestSurveyVersionEntryView(AbstractSurveyTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "contact-survey-version-entries",
            kwargs={"unique_code": "ams-app", "version": "1"},
        )
        questions = Question.objects.all()
        self.payload = {
            "answers": [
                {"question": questions[0].id, "answer": "string"},
                {"question": questions[1].id, "answer": "string"},
            ],
            "entry_point": "city-pass-module",
            "metadata": '{"foo": "bar"}',
        }

    def test_post_survey_version_entry_successfully(self):
        payload = copy.copy(self.payload)
        response = self.client.post(
            self.url, data=payload, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 201)
        self.assertIsInstance(response.data, dict)

    def test_post_survey_version_entry_missing_required_field(self):
        payload = copy.copy(self.payload)
        payload.pop("answers")  # answers is required
        response = self.client.post(
            self.url, data=payload, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 400)
        self.assertIsInstance(response.data, dict)
        self.assertIn("answers", response.data)

    def test_unique_code_not_found(self):
        payload = copy.copy(self.payload)
        url = reverse(
            "contact-survey-version-entries",
            kwargs={"unique_code": "foobar", "version": "1"},
        )
        response = self.client.post(
            url, data=payload, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 404)

    def test_version_not_found(self):
        payload = copy.copy(self.payload)
        url = reverse(
            "contact-survey-version-entries",
            kwargs={"unique_code": "ams-app", "version": "99"},
        )
        response = self.client.post(
            url, data=payload, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 404)

    def test_question_not_found(self):
        payload = copy.copy(self.payload)
        payload["answers"][0]["question"] = 99
        response = self.client.post(
            self.url, data=payload, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 400)
