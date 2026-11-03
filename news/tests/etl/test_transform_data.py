from django.test import TestCase

from news.etl.transform_data import (
    get_article_properties,
    get_body_from_content,
    get_liveblog_messages,
)
from news.tests.mock_data.all_news import (
    BLOG_ARTICLE_368,
    NEWS_ARTICLE_396,
    NEWS_ARTICLE_426,
)


class TransformDataTest(TestCase):
    def test_get_article_properties(self):
        tags = [
            {"id": 531, "name": "Nieuws — Nieuws"},
            {"id": 436, "name": "Nieuws"},
            {"id": 1624, "name": "01 Eindredacteur - Nieuws"},
            {"id": 1720, "name": "Deze week gepubliceerd op Amsterdam.nl"},
            {"id": 1722, "name": "Nu gepubliceerd op Amsterdam.nl"},
            {"id": 411, "name": "migrated"},
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
            {"id": 411, "name": "migrated"},
        ]
        properties = get_article_properties(tags, type="News")

        self.assertEqual(properties["in_all_news"], False)
        self.assertEqual(properties["is_liveblog"], False)
        self.assertEqual(properties["is_district"], True)
        self.assertEqual(properties["district"], "Noord")

    def test_articles_both_in_all_news_and_district(self):
        tags = [
            {"id": 531, "name": "Nieuws — Nieuws"},
            {"id": 436, "name": "Nieuws"},
            {"id": 781, "name": "Nieuws stadsdeel West"},
            {"id": 1624, "name": "01 Eindredacteur - Nieuws"},
            {"id": 1663, "name": "Nieuws stadsdeel West"},
            {"id": 1720, "name": "Deze week gepubliceerd op Amsterdam.nl"},
            {"id": 1722, "name": "Nu gepubliceerd op Amsterdam.nl"},
            {"id": 411, "name": "migrated"},
        ]
        properties = get_article_properties(tags, type="News")

        self.assertEqual(properties["in_all_news"], True)
        self.assertEqual(properties["is_liveblog"], False)
        self.assertEqual(properties["is_district"], True)
        self.assertEqual(properties["district"], "West")

    def test_get_body_from_content(self):
        content = NEWS_ARTICLE_426["content"]
        body = get_body_from_content(content)
        self.assertIn(
            "Sportclubs, sportscholen en buurtinitiatieven organiseren tijdens deze 10 dagen gratis activiteiten in Oost",
            body,
        )

    def test_get_body_from_content_with_empty_content(self):
        content = []
        body = get_body_from_content(content)
        self.assertEqual(body, "")

    def test_get_body_from_content_with_multiple_content_blocks(self):
        content = NEWS_ARTICLE_396["content"]
        body = get_body_from_content(content)
        self.assertIn(
            "Met de campagne Sterker vanaf de start willen we ouders betrouwbare en begrijpelijke informatie over vaccineren geven.",
            body,
        )

    def test_get_liveblog_messages(self):
        blog_entries = BLOG_ARTICLE_368.get("blogEntries", [])
        liveblog_messages = get_liveblog_messages(blog_entries)
        self.assertIsInstance(liveblog_messages, list)
        self.assertEqual(len(liveblog_messages), len(blog_entries))
