from django.test import TestCase

from news.etl.transform_data import get_article_properties


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
