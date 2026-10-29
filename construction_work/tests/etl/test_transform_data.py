from copy import deepcopy
from itertools import chain, repeat
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from requests import HTTPError

from construction_work.etl.transform_data import (
    _transform_article,
    _transform_contacts,
    _transform_project,
    transform_data,
)
from construction_work.tests.mock_data import extracted_data

PROJECT_IMAGE_SET = {
    "id": 12,
    "description": "test",
    "variants": [
        {
            "image": "https://ontw.app.amsterdam.nl/media/image/small.JPEG",
            "width": 320,
            "height": 180,
        },
        {
            "image": "https://ontw.app.amsterdam.nl/media/image/medium.JPEG",
            "width": 768,
            "height": 432,
        },
        {
            "image": "https://ontw.app.amsterdam.nl/media/image/large.JPEG",
            "width": 1280,
            "height": 720,
        },
    ],
}

ARTICLE_IMAGE_SET = {
    "id": 13,
    "description": "test",
    "variants": [
        {
            "image": "https://ontw.app.amsterdam.nl/media/image/small-article.JPEG",
            "width": 320,
            "height": 180,
        },
        {
            "image": "https://ontw.app.amsterdam.nl/media/image/medium-article.JPEG",
            "width": 768,
            "height": 432,
        },
        {
            "image": "https://ontw.app.amsterdam.nl/media/image/large-article.JPEG",
            "width": 1280,
            "height": 720,
        },
    ],
}


@override_settings(
    TIME_ZONE="UTC",
    DVO_URL="https://source.example.invalid/graphql",
)
class TransformDataTestCase(SimpleTestCase):
    @patch("construction_work.etl.transform_data.ImageSetService")
    def test_transforms_extraction_shape_for_ingestion(self, image_set_service):
        image_set_service.return_value.get_or_upload_from_url.return_value = (
            PROJECT_IMAGE_SET
        )
        extracted_payload = deepcopy(extracted_data.MOCK_DATA)

        result = transform_data(extracted_payload)

        self.assertEqual(extracted_payload, extracted_data.MOCK_DATA)
        image_set_service.assert_called_once_with()
        self.assertEqual(
            [project["id"] for project in result["projects"]],
            [project["id"] for project in extracted_data.MOCK_DATA["projects"]],
        )
        self.assertEqual(
            [contact["name"] for contact in result["projects"][0]["contacts"]],
            ["Naam Achternaam", "Jane Smith", "Sarah Johnson"],
        )
        self.assertEqual(
            {article["id"]: article["projectIds"] for article in result["articles"]},
            {10017: [13452], 17549: [13447]},
        )
        self.assertEqual(
            len(image_set_service.return_value.get_or_upload_from_url.call_args_list),
            5,
        )

    @patch("construction_work.etl.transform_data.ImageSetService")
    def test_handles_missing_images_and_news_views(self, image_set_service):
        result = transform_data(
            {
                "projects": [
                    {
                        "id": 1,
                        "title": "No news",
                        "path": "https://example.invalid/no-news",
                        "changedDate": "2026-08-10T09:46:00",
                        "publicationDate": "2021-11-24T13:00:00",
                        "content": [],
                    }
                ],
                "news_articles": {},
                "work_articles": {},
            }
        )

        self.assertEqual(result["articles"], [])
        self.assertIsNone(result["projects"][0]["image_set"])
        self.assertIsNone(result["projects"][0]["timeline"]["title"])
        image_set_service.return_value.get_or_upload_from_url.assert_not_called()

    @patch("construction_work.etl.transform_data.ImageSetService")
    def test_accepts_empty_extraction_result(self, image_set_service):
        self.assertEqual(
            transform_data({"projects": [], "news_articles": {}, "work_articles": {}}),
            {"projects": [], "articles": []},
        )
        image_set_service.assert_called_once_with()

    @patch("construction_work.etl.transform_data.ImageSetService")
    def test_transforms_shared_news_articles_for_multiple_projects(
        self, image_set_service
    ):
        image_set_service.return_value.get_or_upload_from_url.return_value = (
            PROJECT_IMAGE_SET
        )
        extracted_payload = deepcopy(extracted_data.MOCK_DATA)
        second_project = deepcopy(extracted_payload["projects"][0])
        second_project["id"] = 13453
        extracted_payload["projects"].append(second_project)

        result = transform_data(extracted_payload)

        self.assertEqual(
            {article["id"]: article["projectIds"] for article in result["articles"]},
            {10017: [13452, 13453], 17549: [13447]},
        )

    def test_requires_image_service_for_project_and_article_images(self):
        with self.assertRaisesRegex(RuntimeError, "required for project images"):
            _transform_project({"image": [{"src": "/project.jpg"}]}, None)

        with self.assertRaisesRegex(RuntimeError, "required for article images"):
            _transform_article({"image": [{"src": "/article.jpg"}]}, None, "news")

    @patch("construction_work.etl.transform_data.ImageSetService")
    def test_logs_http_error_and_continues_without_image(self, image_set_service):
        image_set_service.return_value.get_or_upload_from_url.side_effect = chain(
            [HTTPError("image service unavailable")], repeat(ARTICLE_IMAGE_SET)
        )

        with self.assertLogs(
            "construction_work.etl.transform_data", level="ERROR"
        ) as logs:
            result = transform_data(deepcopy(extracted_data.MOCK_DATA))

        self.assertIn("Error getting or uploading image", logs.output[0])
        self.assertIsNone(result["projects"][0]["image_set"])
        self.assertEqual(result["articles"][0]["image_set"], ARTICLE_IMAGE_SET)

    @patch("construction_work.etl.transform_data.ImageSetService")
    def test_rejects_image_without_source_path(self, image_set_service):
        extracted_data = {
            "projects": [
                {
                    "id": 1,
                    "title": "Missing image source",
                    "path": "https://example.invalid/missing-image-source",
                    "changedDate": "2026-08-10T09:46:00",
                    "publicationDate": "2021-11-24T13:00:00",
                    "image": [{"name": "missing-source.jpg"}],
                }
            ],
            "news_articles": {},
            "work_articles": {},
        }

        with self.assertRaisesRegex(ValueError, "did not contain a source path"):
            transform_data(extracted_data)
        image_set_service.assert_called_once_with()

    def test_transform_contacts(self):

        block = {
            "__typename": "ParagraphDdsRichText",
            "id": 19989,
            "contentIndication": "contact",
            "content": '<h2>Contact</h2><p><strong>Voornaam Achternaam</strong><br>Position A<br>Extra info<br><a href="mailto:project.osdorpplein@amsterdam.nl">project.osdorpplein@amsterdam.nl</a></p><p><strong>Jane Smith</strong><br>Gebiedsmakelaar wonen<br>Voor vragen over wonen in de buurt, of als u wilt meedenken<br><a href="mailto:jane.smith@amsterdam.nl">jane.smith@amsterdam.nl</a></p><p><strong>Sarah Names</strong><br>Gebiedsmakelaar winkelgebied<br>Voor vragen over het winkelgebied, of als u wilt meedenken<br><a href="mailto:sarah.names@amsterdam.nl">sarah.names@amsterdam.nl</a></p>',
        }

        contacts = _transform_contacts(block["content"])

        self.assertEqual(len(contacts), 3)
        self.assertTrue(all("id" not in contact for contact in contacts))
        self.assertEqual(contacts[0]["name"], "Voornaam Achternaam")
        self.assertEqual(contacts[0]["email"], "project.osdorpplein@amsterdam.nl")
        self.assertEqual(contacts[0]["position"], "Position A")
        self.assertEqual(contacts[0]["extra"], "Extra info")
        self.assertEqual(contacts[1]["name"], "Jane Smith")
        self.assertEqual(contacts[1]["email"], "jane.smith@amsterdam.nl")
        self.assertEqual(contacts[1]["position"], "Gebiedsmakelaar wonen")
        self.assertEqual(
            contacts[1]["extra"],
            "Voor vragen over wonen in de buurt, of als u wilt meedenken",
        )
        self.assertEqual(contacts[2]["name"], "Sarah Names")
        self.assertEqual(contacts[2]["email"], "sarah.names@amsterdam.nl")
        self.assertEqual(contacts[2]["position"], "Gebiedsmakelaar winkelgebied")
        self.assertEqual(
            contacts[2]["extra"],
            "Voor vragen over het winkelgebied, of als u wilt meedenken",
        )
