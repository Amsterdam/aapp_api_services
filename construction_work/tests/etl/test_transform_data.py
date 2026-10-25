from copy import deepcopy
from datetime import datetime
from datetime import timezone as datetime_timezone
from unittest.mock import call, patch

from django.test import SimpleTestCase, override_settings
from requests import HTTPError

from construction_work.etl.transform_data import (
    _transform_article,
    _transform_project,
    transform_data,
)
from construction_work.tests.mock_data.extracted_data import (
    MOCK_EXTRACTED_DATA,
    MOCK_NESTED_CONTENT_AND_SHARED_NEWS_EXTRACTED_DATA,
)

PROJECT_IMAGE_SET = {
    "id": 1001,
    "variants": [{"image": "https://images.example.invalid/project.jpg"}],
}
ARTICLE_IMAGE_SET = {
    "id": 1002,
    "variants": [{"image": "https://images.example.invalid/article.jpg"}],
}


@override_settings(
    TIME_ZONE="UTC",
    DVO_URL="https://source.example.invalid/graphql",
)
class TransformDataTestCase(SimpleTestCase):
    @patch("construction_work.etl.transform_data.ImageSetService")
    def test_transforms_extraction_shape_for_ingestion(self, image_set_service):
        image_set_service.return_value.get_or_upload_from_url.side_effect = [
            PROJECT_IMAGE_SET,
            ARTICLE_IMAGE_SET,
        ]
        extracted_data = deepcopy(MOCK_EXTRACTED_DATA)

        result = transform_data(extracted_data)

        self.assertEqual(extracted_data, MOCK_EXTRACTED_DATA)
        image_set_service.assert_called_once_with()
        image_set_service.return_value.get_or_upload_from_url.assert_has_calls(
            [
                call(
                    "https://source.example.invalid/sites/default/files/mock-project-image.jpg"
                ),
                call(
                    "https://source.example.invalid/sites/default/files/mock-article-image.jpg"
                ),
            ]
        )
        self.assertEqual(
            result["projects"],
            [
                {
                    "id": 101,
                    "title": "Mock bridge project",
                    "subtitle": "Some work to be done",
                    "url": "https://example.invalid/mock-project",
                    "creation_date": datetime(
                        2021, 11, 24, 13, 0, tzinfo=datetime_timezone.utc
                    ),
                    "modification_date": datetime(
                        2026, 8, 10, 9, 46, tzinfo=datetime_timezone.utc
                    ),
                    "publication_date": datetime(
                        2021, 11, 24, 13, 0, tzinfo=datetime_timezone.utc
                    ),
                    "expiration_date": None,
                    "coordinates_lat": 52.37,
                    "coordinates_lon": 4.89,
                    "sections": {
                        "what": [
                            {
                                "body": "<p>Work on the bridge.</p>",
                                "links": [],
                                "title": "Wat",
                            }
                        ],
                        "where": [
                            {
                                "body": "<p>At the mock canal.</p>",
                                "links": [],
                                "title": "Waar",
                            }
                        ],
                        "contact": [
                            {
                                "body": (
                                    "<p><strong>Alex Example</strong><br/>Project "
                                    'manager<br/><a href="mailto:alex@example.invalid">'
                                    "alex@example.invalid</a></p>"
                                ),
                                "links": [
                                    {
                                        "url": "mailto:alex@example.invalid",
                                        "label": "alex@example.invalid",
                                    }
                                ],
                                "title": "Contact",
                            }
                        ],
                    },
                    "contacts": [
                        {
                            "id": 304,
                            "name": "Alex Example",
                            "email": "alex@example.invalid",
                            "phone": None,
                            "position": "Project manager",
                        }
                    ],
                    "timeline": {
                        "title": "Wanneer",
                        "intro": "Mock project planning.",
                        "items": [
                            {
                                "title": "2026",
                                "body": "<p>Work starts.</p>",
                                "collapsed": False,
                                "items": [],
                            }
                        ],
                    },
                    "imageSet": PROJECT_IMAGE_SET,
                }
            ],
        )
        self.assertEqual(
            result["articles"],
            [
                {
                    "id": 601,
                    "title": "Mock project update",
                    "intro": "A short mock article summary.",
                    "body": "<p>Mock article body.</p>",
                    "type": "Mock construction",
                    "url": "https://example.invalid/mock-project-update",
                    "created": datetime(
                        2026, 8, 11, 8, 15, tzinfo=datetime_timezone.utc
                    ),
                    "modified": datetime(
                        2026, 8, 12, 11, 30, tzinfo=datetime_timezone.utc
                    ),
                    "expirationDate": None,
                    "imageSet": ARTICLE_IMAGE_SET,
                    "projectIds": [101],
                }
            ],
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
            }
        )

        self.assertEqual(result["articles"], [])
        self.assertIsNone(result["projects"][0]["imageSet"])
        self.assertIsNone(result["projects"][0]["timeline"]["title"])
        image_set_service.return_value.get_or_upload_from_url.assert_not_called()

    @patch("construction_work.etl.transform_data.ImageSetService")
    def test_accepts_empty_extraction_result(self, image_set_service):
        self.assertEqual(
            transform_data({"projects": [], "news_articles": {}}),
            {"projects": [], "articles": []},
        )
        image_set_service.assert_called_once_with()

    @patch("construction_work.etl.transform_data.ImageSetService")
    def test_transforms_nested_content_and_shared_news_articles(
        self, image_set_service
    ):
        result = transform_data(MOCK_NESTED_CONTENT_AND_SHARED_NEWS_EXTRACTED_DATA)

        first_project = result["projects"][0]
        self.assertEqual(first_project["title"], "")
        self.assertIsNone(first_project["subtitle"])
        self.assertEqual(
            first_project["creation_date"],
            datetime(2024, 1, 2, tzinfo=datetime_timezone.utc),
        )
        self.assertIsNone(first_project["modification_date"])
        self.assertEqual(first_project["coordinates_lat"], 52.3)
        self.assertEqual(first_project["coordinates_lon"], 4.9)
        self.assertEqual(first_project["sections"]["where"][0]["title"], "Waar")
        self.assertEqual(
            first_project["sections"]["where"][0]["body"],
            '<p><a href="/route">Route</a></p>',
        )
        self.assertEqual(
            first_project["contacts"],
            [
                {
                    "id": 12,
                    "name": "Sam Example",
                    "email": None,
                    "phone": "+31201234",
                    "position": "Manager",
                }
            ],
        )
        self.assertEqual(
            first_project["timeline"]["items"][0]["items"][0]["title"], "Substage"
        )
        self.assertIsNone(result["projects"][1]["coordinates_lat"])
        self.assertEqual(result["articles"][0]["body"], "<p>Article body</p>")
        self.assertEqual(result["articles"][0]["type"], "Notice")
        self.assertEqual(result["articles"][0]["projectIds"], [5, 6])
        self.assertIsNone(result["articles"][1]["type"])
        self.assertEqual(result["articles"][1]["projectIds"], [5, 6])
        image_set_service.return_value.get_or_upload_from_url.assert_not_called()

    def test_requires_image_service_for_project_and_article_images(self):
        with self.assertRaisesRegex(RuntimeError, "required for project images"):
            _transform_project({"image": [{"src": "/project.jpg"}]}, None)

        with self.assertRaisesRegex(RuntimeError, "required for article images"):
            _transform_article({"image": [{"src": "/article.jpg"}]}, None)

    @patch("construction_work.etl.transform_data.ImageSetService")
    def test_logs_http_error_and_continues_without_image(self, image_set_service):
        image_set_service.return_value.get_or_upload_from_url.side_effect = [
            HTTPError("image service unavailable"),
            ARTICLE_IMAGE_SET,
        ]

        with self.assertLogs(
            "construction_work.etl.transform_data", level="ERROR"
        ) as logs:
            result = transform_data(MOCK_EXTRACTED_DATA)

        self.assertIn("Error getting or uploading image", logs.output[0])
        self.assertIsNone(result["projects"][0]["imageSet"])
        self.assertEqual(result["articles"][0]["imageSet"], ARTICLE_IMAGE_SET)

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
        }

        with self.assertRaisesRegex(ValueError, "did not contain a source path"):
            transform_data(extracted_data)
        image_set_service.assert_called_once_with()
