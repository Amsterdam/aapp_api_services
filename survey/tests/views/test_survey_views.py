import copy

from django.core.management import call_command
from django.urls import reverse

from core.tests.test_authentication import BasicAPITestCase
from survey.models import Question, Survey, SurveyConfiguration, SurveyVersion


class AbstractSurveyTestCase(BasicAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("surveymockdata")


class TestSurveyView(AbstractSurveyTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("survey-surveys")

    def test_get_surveys_successfully(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)


class TestSurveyConfigView(AbstractSurveyTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("survey-config", kwargs={"location": "aapp-contact"})
        SurveyConfiguration.objects.create(
            location="aapp-contact", survey=Survey.objects.get(unique_code="ams-app")
        )

    def test_get_surveys_successfully(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_surveys_unknown_location(self):
        url = reverse("survey-config", kwargs={"location": "foobar"})
        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 404)


class TestSurveyVersionView(AbstractSurveyTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("survey-versions", kwargs={"unique_code": "ams-app"})

    def test_get_survey_versions_successfully(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)

    def test_unique_code_not_found(self):
        url = reverse("survey-versions", kwargs={"unique_code": "foobar"})
        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 404)


class TestSurveyVersionDetailView(AbstractSurveyTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "survey-version-detail",
            kwargs={"unique_code": "ams-app", "version": "1"},
        )

    def test_get_survey_version_detail_successfully(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data["version"], 1)

    def test_unique_code_not_found(self):
        url = reverse(
            "survey-version-detail",
            kwargs={"unique_code": "foobar", "version": "1"},
        )
        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 404)

    def test_version_not_found(self):
        url = reverse(
            "survey-version-detail",
            kwargs={"unique_code": "ams-app", "version": "99"},
        )
        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 404)


class TestSurveyVersionLatestView(AbstractSurveyTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("survey-version-latest", kwargs={"unique_code": "ams-app"})

    def test_get_survey_version_latest_successfully(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data["version"], 1)

    def test_unique_code_not_found(self):
        url = reverse("survey-version-latest", kwargs={"unique_code": "foobar"})
        response = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response.status_code, 404)


class TestSurveyVersionEntryView(AbstractSurveyTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "survey-version-entries",
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
            "survey-version-entries",
            kwargs={"unique_code": "foobar", "version": "1"},
        )
        response = self.client.post(
            url, data=payload, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 404)

    def test_version_not_found(self):
        payload = copy.copy(self.payload)
        url = reverse(
            "survey-version-entries",
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


class TestSurveyVersionEntryListView(AbstractSurveyTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("survey-entries-list")
        self.survey_version = SurveyVersion.objects.first().version
        test_entry_payload = {
            "answers": [
                {"question": q.id, "answer": "string"} for q in Question.objects.all()
            ],
            "entry_point": "Parkeer module",
            "metadata": {
                "app_version": "1.0.0",
            },
        }
        for _i in range(9):
            self.client.post(
                reverse(
                    "survey-version-entries",
                    kwargs={"unique_code": "ams-app", "version": self.survey_version},
                ),
                data=test_entry_payload,
                format="json",
                headers=self.api_headers,
            )

    def test_get_successfully(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 9)

    def test_get_first_page(self):
        data = {"page": 1, "page_size": 5}
        response = self.client.get(self.url, data, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNotNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_get_second_page(self):
        data = {"page": 2, "page_size": 5}
        response = self.client.get(self.url, data, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 4)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNotNone(response.data.get("previous"))

    def test_get_wrong_page(self):
        data = {"page": 3, "page_size": 5}
        response = self.client.get(self.url, data, headers=self.api_headers)
        self.assertEqual(response.status_code, 404)

    def test_get_survey_unique_code_filter(self):
        data = {"survey_unique_code": "ams-app"}
        response = self.client.get(self.url, data, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 9)

    def test_get_survey_unique_code_filter_empty(self):
        data = {"survey_unique_code": "foobar"}
        response = self.client.get(self.url, data, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 0)

    def test_get_survey_version_filter(self):
        data = {"survey_unique_code": "ams-app", "survey_version": self.survey_version}
        response = self.client.get(self.url, data, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 9)

    def test_get_survey_version_filter_empty(self):
        data = {"survey_version": "2"}
        response = self.client.get(self.url, data, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 0)
