from django.test import TestCase, override_settings

from news.etl.transform_data import (
    get_article_properties,
    get_body_from_content,
    get_liveblog_messages,
    transform,
)
from news.tests.mock_data.all_news import (
    BLOG_ARTICLE_368,
    NEWS_ARTICLE_396,
    NEWS_ARTICLE_426,
)


class TransformDataTest(TestCase):
    def test_transform_skips_articles_missing_required_fields(self):
        article = {
            "id": 123,
            "__typename": "News",
            "title": "A title",
            "publicationDate": "2026-11-01T13:00:00Z",
            "changedDate": "2026-11-06T09:00:00Z",
            "path": "https://example.com/article",
        }
        required_fields = ("id", "title", "changedDate", "publicationDate", "path")
        incomplete_articles = [{**article, field: None} for field in required_fields]

        with self.assertLogs("news.etl.transform_data", level="WARNING") as logs:
            transformed = transform([*incomplete_articles, article])

        self.assertEqual([item["foreign_id"] for item in transformed], [123])
        self.assertEqual(
            [record.missing_fields for record in logs.records],
            [[field] for field in required_fields],
        )

    def test_get_article_properties(self):
        tags = [
            {"id": 531, "name": "Nieuws — Nieuws"},
            {"id": 436, "name": "Nieuws"},
            {"id": 1624, "name": "Some Tag"},
        ]

        properties = get_article_properties(tags, type="Blog")

        self.assertEqual(properties["in_all_news"], True)
        self.assertEqual(properties["is_liveblog"], True)
        self.assertEqual(properties["is_district"], False)
        self.assertEqual(properties["district"], None)

    def test_get_article_properties_with_district_tag(self):
        tags = [
            {"id": 779, "name": "Nieuws stadsdeel Noord"},
            {"id": 1656, "name": "Nieuws stadsdeel Noord"},
        ]
        properties = get_article_properties(tags, type="News")

        self.assertEqual(properties["in_all_news"], False)
        self.assertEqual(properties["is_liveblog"], False)
        self.assertEqual(properties["is_district"], True)
        self.assertEqual(properties["district"], "noord")

    def test_articles_both_in_all_news_and_district(self):
        tags = [
            {"id": 531, "name": "Nieuws — Nieuws"},
            {"id": 123, "name": "Nieuws"},
            {"id": 781, "name": "Nieuws stadsdeel West"},
            {"id": 827, "name": "01 Eindredacteur - Nieuws"},
        ]
        properties = get_article_properties(tags, type="News")

        self.assertEqual(properties["in_all_news"], True)
        self.assertEqual(properties["is_liveblog"], False)
        self.assertEqual(properties["is_district"], True)
        self.assertEqual(properties["district"], "west")

    def test_get_body_from_content(self):
        content = NEWS_ARTICLE_426["content"]
        body = get_body_from_content(content, foreign_id=426)
        self.assertIn(
            "Sportclubs, sportscholen en buurtinitiatieven organiseren tijdens deze 10 dagen gratis activiteiten in Oost",
            body,
        )

    def test_get_body_from_content_with_empty_content(self):
        content = []
        body = get_body_from_content(content, foreign_id=0)
        self.assertEqual(body, "")

    def test_get_body_from_content_with_multiple_content_blocks(self):
        content = NEWS_ARTICLE_396["content"]
        body = get_body_from_content(content, foreign_id=396)
        self.assertIn(
            "Met de campagne Sterker vanaf de start willen we ouders betrouwbare en begrijpelijke informatie over vaccineren geven.",
            body,
        )

    def test_get_liveblog_messages(self):
        blog_entries = BLOG_ARTICLE_368.get("blogEntries", [])
        liveblog_messages = get_liveblog_messages(blog_entries)
        self.assertIsInstance(liveblog_messages, list)
        self.assertEqual(len(liveblog_messages), len(blog_entries))

    @override_settings(DVO_URL="https://dvo.example.test")
    def test_get_liveblog_messages_uses_first_image_across_content_blocks(self):
        blog_entries = [
            {
                "content": [
                    {
                        "text": '<div class="dds-prose"><p class="dds-paragraph"><span>Lorem ipsum dolor sit amet</span></p></div>'
                    },
                    {
                        "text": '<div class="dds-prose"><p class="dds-paragraph">Sed commodo volutpat nibh sed ullamcorper.</p></div>',
                        "image": [
                            {
                                "src": "/image.jpg",
                                "alt": "Image alt",
                                "description": "Image description",
                            }
                        ],
                    },
                ]
            }
        ]

        message = get_liveblog_messages(blog_entries)[0]

        self.assertEqual(
            message["body"],
            '<p class="dds-paragraph"><span>Lorem ipsum dolor sit amet</span></p><p class="dds-paragraph">Sed commodo volutpat nibh sed ullamcorper.</p>',
        )
        self.assertEqual(
            message["image"],
            {
                "url": "https://dvo.example.test/image.jpg",
                "alt": "Image alt",
                "description": "Image description",
            },
        )
