from copy import deepcopy
from datetime import datetime
from datetime import timezone as datetime_timezone
from unittest.mock import call, patch

from django.test import SimpleTestCase, override_settings
from requests import HTTPError

from construction_work.etl.transform_data import transform_data
from construction_work.tests.mock_data.extracted_data import MOCK_EXTRACTED_DATA

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
                    "subtitle": "A short mock project summary.",
                    "url": "https://example.invalid/mock-project",
                    "created": datetime(
                        2021, 11, 24, 13, 0, tzinfo=datetime_timezone.utc
                    ),
                    "modified": datetime(
                        2026, 8, 10, 9, 46, tzinfo=datetime_timezone.utc
                    ),
                    "publicationDate": datetime(
                        2021, 11, 24, 13, 0, tzinfo=datetime_timezone.utc
                    ),
                    "expirationDate": None,
                    "coordinates": {"lat": 52.37, "lon": 4.89},
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

    def test_handles_missing_images_and_news_views(self):
        result = transform_data(
            {
                "projects": [{"id": 1, "title": "No news", "content": []}],
                "news_articles": {},
            }
        )

        self.assertEqual(result["articles"], [])
        self.assertIsNone(result["projects"][0]["imageSet"])
        self.assertIsNone(result["projects"][0]["timeline"]["title"])

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

    def test_rejects_image_without_source_path(self):
        extracted_data = {
            "projects": [{"id": 1, "image": [{"name": "missing-source.jpg"}]}],
            "news_articles": {},
        }

        with self.assertRaisesRegex(ValueError, "did not contain a source path"):
            transform_data(extracted_data)
