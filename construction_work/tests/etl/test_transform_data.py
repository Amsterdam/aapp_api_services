from datetime import datetime

from django.conf import settings
from django.test import TestCase, override_settings

from construction_work.etl.transform_data import _image, _images, articles, projects


@override_settings(
    DATE_FORMAT_IPROX="%Y-%m-%dT%H:%M:%S%z", EPOCH="1970-01-01T00:00:00+0000"
)
class TransformDataTestCase(TestCase):
    def test_projects_transforms_data_correctly(self):
        # Prepare test data
        data = [
            {
                "id": 1,
                "title": "Project 1",
                "image": {
                    "sources": [
                        {"url": "http://example.com/image1.jpg"},
                        {"url": "http://example.com/image2.jpg"},
                    ]
                },
                "images": [
                    {
                        "sources": [
                            {"url": "http://example.com/image3.jpg"},
                            {"url": "http://example.com/image4.jpg"},
                        ]
                    },
                    {"sources": [{"url": "http://example.com/image5.jpg"}]},
                ],
                "modified": "2021-10-01T12:34:56+0000",
            }
        ]

        # Expected transformed data
        expected_data = [
            {
                "id": 1,
                "title": "Project 1",
                "image": {
                    "sources": [
                        {"uri": "http://example.com/image1.jpg"},
                        {"uri": "http://example.com/image2.jpg"},
                    ]
                },
                "images": [
                    {
                        "sources": [
                            {"uri": "http://example.com/image3.jpg"},
                            {"uri": "http://example.com/image4.jpg"},
                        ]
                    },
                    {"sources": [{"uri": "http://example.com/image5.jpg"}]},
                ],
                "modified": datetime.strptime(
                    "2021-10-01T12:34:56+0000", settings.DATE_FORMAT_IPROX
                ),
            }
        ]

        projects(data)
        self.assertEqual(data, expected_data)

    def test_articles_transforms_data_correctly(self):
        data = [
            {
                "id": 100,
                "title": "Article 1",
                "image": {
                    "sources": [
                        {"url": "http://example.com/article_image1.jpg"},
                        {"url": "http://example.com/article_image2.jpg"},
                    ]
                },
                "modified": "2021-10-02T13:45:00+0000",
            }
        ]

        expected_data = [
            {
                "id": 100,
                "title": "Article 1",
                "image": {
                    "sources": [
                        {"uri": "http://example.com/article_image1.jpg"},
                        {"uri": "http://example.com/article_image2.jpg"},
                    ]
                },
                "modified": datetime.strptime(
                    "2021-10-02T13:45:00+0000", settings.DATE_FORMAT_IPROX
                ),
            }
        ]

        articles(data)
        self.assertEqual(data, expected_data)

    def test_projects_handles_missing_fields(self):
        data = [{"id": 2, "title": "Project 2", "modified": "2021-10-03T14:00:00+0000"}]
        expected_data = [
            {
                "id": 2,
                "title": "Project 2",
                "modified": datetime.strptime(
                    "2021-10-03T14:00:00+0000", settings.DATE_FORMAT_IPROX
                ),
            }
        ]

        projects(data)
        self.assertEqual(data, expected_data)

    def test_articles_handles_missing_image(self):
        data = [
            {"id": 101, "title": "Article 2", "modified": "2021-10-04T15:30:00+0000"}
        ]
        expected_data = [
            {
                "id": 101,
                "title": "Article 2",
                "modified": datetime.strptime(
                    "2021-10-04T15:30:00+0000", settings.DATE_FORMAT_IPROX
                ),
            }
        ]

        articles(data)
        self.assertEqual(data, expected_data)

    def test_projects_handles_missing_modified_date(self):
        data = [
            {
                "id": 3,
                "title": "Project 3",
                "image": {"sources": [{"url": "http://example.com/image6.jpg"}]},
                "images": [{"sources": [{"url": "http://example.com/image7.jpg"}]}],
                # 'modified' field is missing
            }
        ]
        expected_modified = datetime.strptime(
            settings.EPOCH, settings.DATE_FORMAT_IPROX
        )

        expected_data = [
            {
                "id": 3,
                "title": "Project 3",
                "image": {"sources": [{"uri": "http://example.com/image6.jpg"}]},
                "images": [{"sources": [{"uri": "http://example.com/image7.jpg"}]}],
                "modified": expected_modified,
            }
        ]

        projects(data)
        self.assertEqual(data, expected_data)

    def test_articles_handles_incorrect_date_format(self):
        data = [{"id": 102, "title": "Article 3", "modified": "2021/10/05 16:00:00"}]
        with self.assertRaises(ValueError):
            articles(data)

    def test_image_transforms_url_to_uri(self):
        image_set = {
            "sources": [
                {"url": "http://example.com/image8.jpg"},
                {"url": "http://example.com/image9.jpg"},
            ]
        }
        expected_image_set = {
            "sources": [
                {"uri": "http://example.com/image8.jpg"},
                {"uri": "http://example.com/image9.jpg"},
            ]
        }

        result = _image(image_set)
        self.assertEqual(result, expected_image_set)

    def test_image_handles_missing_sources(self):
        image_set = {}
        expected_image_set = {}

        result = _image(image_set)
        self.assertEqual(result, expected_image_set)

    def test_images_transforms_list_of_images(self):
        images_set = [
            {"sources": [{"url": "http://example.com/image10.jpg"}]},
            {"sources": [{"url": "http://example.com/image11.jpg"}]},
        ]
        expected_images_set = [
            {"sources": [{"uri": "http://example.com/image10.jpg"}]},
            {"sources": [{"uri": "http://example.com/image11.jpg"}]},
        ]

        result = _images(images_set)
        self.assertEqual(result, expected_images_set)

    def test_projects_with_no_data(self):
        data = []
        projects(data)

        self.assertEqual(data, [])

    def test_articles_with_no_data(self):
        data = []
        articles(data)

        self.assertEqual(data, [])

    def test_projects_handles_null_image_fields(self):
        data = [
            {
                "id": 4,
                "title": "Project 4",
                "image": None,
                "images": None,
                "modified": "2021-10-06T17:15:00+0000",
            }
        ]
        expected_data = [
            {
                "id": 4,
                "title": "Project 4",
                "modified": datetime.strptime(
                    "2021-10-06T17:15:00+0000", settings.DATE_FORMAT_IPROX
                ),
            }
        ]

        projects(data)
        # Remove 'image' and 'images' keys since they are None
        data[0].pop("image", None)
        data[0].pop("images", None)
        self.assertEqual(data, expected_data)

    def test_image_handles_empty_sources_list(self):
        image_set = {"sources": []}
        expected_image_set = {"sources": []}

        result = _image(image_set)
        self.assertEqual(result, expected_image_set)
