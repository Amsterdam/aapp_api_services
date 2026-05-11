import httpx
import respx
from django.test import TestCase
from model_bakery import baker

from news.etl.extract_data import IproxFetcher
from news.models import NewsArticle
from news.tests.mock_data import highlighted, item_article, liveblogs


class ExtractDataTest(TestCase):
    def setUp(self):
        self.fetch_url = "https://api.example.com/fetch/"
        self.detail_url = "https://api.example.com/detail/"
        

    def test_fetch_all_items_single_source(self):
        resp = respx.get(f"{self.fetch_url}/highlighted").mock(
            return_value=httpx.Response(200, json=highlighted.MOCK_RESPONSE)
        )
        # Simulate no sources (default fetch)
        fetcher = IproxFetcher(self.fetch_url, self.detail_url, is_paginated=True)

        items = fetcher.fetch_all_items()
        self.assertEqual(resp.call_count, 1)
        self.assertIsInstance(items, dict)
        self.assertIn(1101234, items)
        self.assertIn(1101235, items)
        self.assertEqual(items[1101234]["type"], None)
        self.assertEqual(items[1101234]["district"], None)

    def test_fetch_all_items_multiple_sources(self):
        resp_highlighted = respx.get(f"{self.fetch_url}/highlighted?page=0").mock(
            return_value=httpx.Response(200, json=highlighted.MOCK_RESPONSE)
        )
        resp_liveblogs = respx.get(f"{self.fetch_url}/liveblogs?page=0").mock(
            return_value=httpx.Response(200, json=liveblogs.MOCK_RESPONSE)
        )
        sources = [
            {"index": "highlighted", "type": "highlighted", "district": None},
            {"index": "liveblogs", "type": "liveblog", "district": None},
        ]
        fetcher = IproxFetcher(
            self.fetch_url, self.detail_url, sources=sources, is_paginated=True
        )

        items = fetcher.fetch_all_items()
        self.assertEqual(resp_highlighted.call_count, 1)
        self.assertEqual(resp_liveblogs.call_count, 1)
        self.assertIsInstance(items, dict)
        self.assertIn(1101234, items)
        self.assertIn(1321234, items)
        self.assertEqual(items[1101234]["type"], "highlighted")
        self.assertEqual(items[1321234]["type"], "liveblog")

    def test_fetch_items_data_merges_details(self):
        resp_highlighted_detail_1 = respx.get(f"{self.detail_url}/1101234").mock(
            return_value=httpx.Response(200, json=item_article.MOCK_RESPONSE)
        )
        resp_highlighted_detail_2 = respx.get(f"{self.detail_url}/1101235").mock(
            return_value=httpx.Response(200, json=item_article.MOCK_RESPONSE)
        )
        sources = [
            {"index": "highlighted", "type": "highlighted", "district": None}
        ]
        fetcher = IproxFetcher(self.fetch_url, self.detail_url, sources=sources, is_paginated=True)
        # Prepare items dict
        items = {
            1101234: {"id": 1101234, "type": "highlighted", "district": None},
            1101235: {"id": 1101235, "type": "highlighted", "district": None},
        }

        result = fetcher.fetch_items_data(items)
        self.assertEqual(resp_highlighted_detail_1.call_count, 1)
        self.assertEqual(resp_highlighted_detail_2.call_count, 1)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], item_article.MOCK_RESPONSE["title"])
        self.assertEqual(result[0]["type"], "highlighted")
        self.assertEqual(result[0]["district"], None)
        self.assertEqual(result[1]["title"], item_article.MOCK_RESPONSE["title"])
        self.assertEqual(result[1]["type"], "highlighted")
        self.assertEqual(result[1]["district"], None)

    def test_is_altered(self):
        # db_item and item are dicts with relevant fields
        db_item = {
            "creation_date": "2024-01-01",
            "modification_date": "2024-01-02",
            "publication_date": "2024-01-03",
            "expiration_date": "2024-01-04",
            "type": "highlighted",
            "district": None,
        }
        # No change
        item = {
            "created": "2024-01-01",
            "modified": "2024-01-02",
            "publication_date": "2024-01-03",
            "expiration_date": "2024-01-04",
            "type": "highlighted",
            "district": None,
        }
        self.assertFalse(IproxFetcher.is_altered(db_item, item))
        # Change in modification_date
        item2 = dict(item)
        item2["modified"] = "2024-01-05"
        self.assertTrue(IproxFetcher.is_altered(db_item, item2))
        # Change in type
        item3 = dict(item)
        item3["type"] = "liveblog"
        self.assertTrue(IproxFetcher.is_altered(db_item, item3))

    def test_extract_new(self):
        resp_highlighted = respx.get(f"{self.fetch_url}/highlighted?page=0").mock(
            return_value=httpx.Response(200, json=highlighted.MOCK_RESPONSE)
        )
        resp_highlighted_detail = respx.get(f"{self.detail_url}/1101234").mock(
            return_value=httpx.Response(200, json=item_article.MOCK_RESPONSE)
        )
        resp_highlighted_detail_2 = respx.get(f"{self.detail_url}/1101235").mock(
            return_value=httpx.Response(200, json=item_article.MOCK_RESPONSE)
        )
        sources = [
            {"index": "highlighted", "type": "highlighted", "district": None}
        ]
        fetcher = IproxFetcher(self.fetch_url, self.detail_url, sources=sources, is_paginated=True)

        result = fetcher.extract()

        self.assertEqual(resp_highlighted.call_count, 1)
        self.assertEqual(resp_highlighted_detail.call_count, 1)
        self.assertEqual(resp_highlighted_detail_2.call_count, 1)
        self.assertEqual(len(result), 2)

    def test_extract_altered(self):
        baker.make(NewsArticle, foreign_id=1101234, modification_date="2024-01-01")
        resp_highlighted = respx.get(f"{self.fetch_url}/highlighted?page=0").mock(
            return_value=httpx.Response(200, json=highlighted.MOCK_RESPONSE)
        )
        resp_highlighted_detail = respx.get(f"{self.detail_url}/1101234").mock(
            return_value=httpx.Response(200, json=item_article.MOCK_RESPONSE)
        )
        resp_highlighted_detail_2 = respx.get(f"{self.detail_url}/1101235").mock(
            return_value=httpx.Response(200, json=item_article.MOCK_RESPONSE)
        )
        sources = [
            {"index": "highlighted", "type": "highlighted", "district": None}
        ]
        fetcher = IproxFetcher(self.fetch_url, self.detail_url, sources=sources, is_paginated=True)

        result = fetcher.extract()
        self.assertEqual(resp_highlighted.call_count, 1)
        self.assertEqual(resp_highlighted_detail.call_count, 1)
        self.assertEqual(resp_highlighted_detail_2.call_count, 1)
        self.assertEqual(len(result), 2)
