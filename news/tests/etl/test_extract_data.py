from datetime import datetime

from aioresponses import aioresponses
from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from news.etl.extract_data import IproxFetcher
from news.models import NewsArticle
from news.tests.mock_data import highlighted, item_article, liveblogs


class ExtractDataTest(TestCase):
    def setUp(self):
        self.fetch_url = "https://api.example.com/fetch"
        self.detail_url = "https://api.example.com/detail"

    def test_fetch_all_items_single_source(self):
        # Simulate no sources (default fetch)
        fetcher = IproxFetcher(self.fetch_url, self.detail_url, is_paginated=True)

        with aioresponses() as mocked:
            mocked.get(
                f"{self.fetch_url}",
                payload=highlighted.MOCK_RESPONSE,
            )
            print("Mocked URL:", f"{self.fetch_url}")

            items = fetcher.fetch_all_items()
            self.assertIsInstance(items, dict)
            self.assertIn(123123, items)
            self.assertIn(123124, items)
            self.assertEqual(items[123123]["type"], None)
            self.assertEqual(items[123123]["district"], None)

    def test_fetch_all_items_multiple_sources(self):
        sources = [
            {"index": "highlighted", "type": "highlighted", "district": None},
            {"index": "liveblogs", "type": "liveblog", "district": None},
        ]
        fetcher = IproxFetcher(
            self.fetch_url, self.detail_url, sources=sources, is_paginated=True
        )

        with aioresponses() as mocked:
            mocked.get(
                f"{self.fetch_url}/highlighted?page=0",
                payload=highlighted.MOCK_RESPONSE,
            )
            print("Mocked URL:", f"{self.fetch_url}/highlighted?page=0")
            mocked.get(
                f"{self.fetch_url}/liveblogs?page=0", payload=liveblogs.MOCK_RESPONSE
            )
            print("Mocked URL:", f"{self.fetch_url}/liveblogs?page=0")
            items = fetcher.fetch_all_items()
            self.assertIsInstance(items, dict)
            self.assertIn(123124, items)
            self.assertIn(1321235, items)
            self.assertEqual(items[123124]["type"], "highlighted")
            self.assertEqual(items[1321235]["type"], "liveblog")

    def test_fetch_items_data_merges_details(self):
        sources = [{"index": "highlighted", "type": "highlighted", "district": None}]
        fetcher = IproxFetcher(
            self.fetch_url, self.detail_url, sources=sources, is_paginated=True
        )
        # Prepare items dict
        items = {
            123123: {"id": 123123, "type": "highlighted", "district": None},
            123124: {"id": 123124, "type": "highlighted", "district": None},
        }
        with aioresponses() as mocked:
            mocked.get(
                f"{self.detail_url}/123123", payload=item_article.MOCK_RESPONSE_123123
            )
            mocked.get(
                f"{self.detail_url}/123124", payload=item_article.MOCK_RESPONSE_123124
            )

            result = fetcher.fetch_items_data(items)
            self.assertEqual(len(result), 2)
            self.assertEqual(
                result[0]["title"], item_article.MOCK_RESPONSE_123123["title"]
            )
            self.assertEqual(result[0]["type"], "highlighted")
            self.assertEqual(result[0]["district"], None)
            self.assertEqual(
                result[1]["title"], item_article.MOCK_RESPONSE_123124["title"]
            )
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
        sources = [{"index": "highlighted", "type": "highlighted", "district": None}]
        fetcher = IproxFetcher(
            self.fetch_url, self.detail_url, sources=sources, is_paginated=True
        )
        with aioresponses() as mocked:
            mocked.get(
                f"{self.fetch_url}/highlighted?page=0",
                payload=highlighted.MOCK_RESPONSE,
            )
            print("Mocked URL:", f"{self.fetch_url}/highlighted?page=0")
            mocked.get(
                f"{self.detail_url}/123123", payload=item_article.MOCK_RESPONSE_123123
            )
            mocked.get(
                f"{self.detail_url}/123124", payload=item_article.MOCK_RESPONSE_123124
            )
            result = fetcher.extract()
            self.assertEqual(len(result), 2)

    def test_extract_altered(self):
        """
        Simulate an existing article with an older modification date, so it should be extracted 
        as altered.
        The other article is new and should also be extracted, so we expect 2 results.
        """
        baker.make(NewsArticle, foreign_id=123123, modification_date="2024-01-01")
        sources = [{"index": "highlighted", "type": "highlighted", "district": None}]
        fetcher = IproxFetcher(
            self.fetch_url, self.detail_url, sources=sources, is_paginated=True
        )

        with aioresponses() as mocked:
            mocked.get(
                f"{self.fetch_url}/highlighted?page=0",
                payload=highlighted.MOCK_RESPONSE,
            )
            mocked.get(
                f"{self.detail_url}/123123", payload=item_article.MOCK_RESPONSE_123123
            )
            mocked.get(
                f"{self.detail_url}/123124", payload=item_article.MOCK_RESPONSE_123124
            )

            result = fetcher.extract()
            self.assertEqual(len(result), 2)

    def test_extract_one_new(self):
        baker.make(
            NewsArticle,
            foreign_id=123123,
            modification_date=datetime(2018, 7, 4, 6, 49, tzinfo=timezone.UTC),
            creation_date=datetime(2018, 7, 3, 6, 49, tzinfo=timezone.UTC),
            publication_date=datetime(2026, 5, 8, 8, 13, tzinfo=timezone.UTC),
            type="highlighted",
            district=None,
        )
        sources = [{"index": "highlighted", "type": "highlighted", "district": None}]
        fetcher = IproxFetcher(
            self.fetch_url, self.detail_url, sources=sources, is_paginated=True
        )

        with aioresponses() as mocked:
            mocked.get(
                f"{self.fetch_url}/highlighted?page=0",
                payload=highlighted.MOCK_RESPONSE,
            )
            mocked.get(
                f"{self.detail_url}/123123", payload=item_article.MOCK_RESPONSE_123123
            )
            mocked.get(
                f"{self.detail_url}/123124", payload=item_article.MOCK_RESPONSE_123124
            )

            result = fetcher.extract()
            print(result)
            self.assertEqual(len(result), 1)
