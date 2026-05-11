from unittest.mock import AsyncMock, patch

from django.test import TestCase

from news.etl.extract_data import IproxFetcher
from news.tests.mock_data import highlighted, liveblogs


class ExtractDataTest(TestCase):
    def setUp(self):
        self.fetch_url = "https://api.example.com/fetch/"
        self.detail_url = "https://api.example.com/detail/"
        self.sources = [
            {"index": "highlighted", "type": "highlighted", "district": None},
            {"index": "liveblogs", "type": "liveblog", "district": None},
        ]

    @patch("news.etl.extract_data.IproxFetcher._async_fetch", new_callable=AsyncMock)
    def test_fetch_all_items_single_source(self, mock_async_fetch):
        # Simulate no sources (default fetch)
        fetcher = IproxFetcher(self.fetch_url, self.detail_url, is_paginated=True)
        # Return highlighted mock data
        mock_async_fetch.return_value = highlighted.MOCK_RESPONSE

        items = fetcher.fetch_all_items()
        self.assertIsInstance(items, dict)
        self.assertIn(1101234, items)
        self.assertIn(1101235, items)
        self.assertEqual(items[1101234]["type"], None)
        self.assertEqual(items[1101234]["district"], None)

    @patch("news.etl.extract_data.IproxFetcher._async_fetch", new_callable=AsyncMock)
    def test_fetch_all_items_multiple_sources(self, mock_async_fetch):
        fetcher = IproxFetcher(
            self.fetch_url, self.detail_url, sources=self.sources, is_paginated=True
        )
        # Return highlighted for first, liveblogs for second
        mock_async_fetch.side_effect = [
            highlighted.MOCK_RESPONSE,
            liveblogs.MOCK_RESPONSE,
        ]

        items = fetcher.fetch_all_items()
        self.assertIsInstance(items, dict)
        self.assertIn(1101234, items)
        self.assertIn(1321234, items)
        self.assertEqual(items[1101234]["type"], "highlighted")
        self.assertEqual(items[1321234]["type"], "liveblog")

    @patch("news.etl.extract_data.IproxFetcher._async_fetch", new_callable=AsyncMock)
    def test_fetch_items_data_merges_details(self, mock_async_fetch):
        fetcher = IproxFetcher(self.fetch_url, self.detail_url, is_paginated=True)
        # Prepare items dict
        items = {
            1101234: {"id": 1101234, "type": "highlighted", "district": None},
            1101235: {"id": 1101235, "type": "highlighted", "district": None},
        }
        # Mock detail responses
        detail_data = [
            {"id": 1101234, "extra": "foo"},
            {"id": 1101235, "extra": "bar"},
        ]
        mock_async_fetch.return_value = detail_data
        result = fetcher.fetch_items_data(items)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["extra"], "foo")
        self.assertEqual(result[0]["type"], "highlighted")
        self.assertEqual(result[0]["district"], None)
        self.assertEqual(result[1]["extra"], "bar")

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

    @patch("news.etl.extract_data.IproxFetcher.fetch_all_items")
    @patch("news.etl.extract_data.IproxFetcher.fetch_items_data")
    def test_extract(self, mock_fetch_items_data, mock_fetch_all_items):
        fetcher = IproxFetcher(self.fetch_url, self.detail_url, is_paginated=True)
        # Simulate all_iprox_items and db_articles
        mock_fetch_all_items.return_value = {
            1: {
                "id": 1,
                "created": "2024-01-01",
                "modified": "2024-01-02",
                "publication_date": "2024-01-03",
                "expiration_date": "2024-01-04",
                "type": "highlighted",
                "district": None,
            },
            2: {
                "id": 2,
                "created": "2024-01-01",
                "modified": "2024-01-02",
                "publication_date": "2024-01-03",
                "expiration_date": "2024-01-04",
                "type": "highlighted",
                "district": None,
            },
        }
        # Patch NewsArticle.objects.values to simulate DB
        with patch("news.etl.extract_data.NewsArticle.objects.values") as mock_values:
            mock_values.return_value = [
                {
                    "foreign_id": 1,
                    "creation_date": "2024-01-01",
                    "modification_date": "2024-01-02",
                    "publication_date": "2024-01-03",
                    "expiration_date": "2024-01-04",
                    "type": "highlighted",
                    "district": None,
                },
            ]
            # Only item 2 is new
            mock_fetch_items_data.return_value = [
                {
                    "id": 2,
                    "created": "2024-01-01",
                    "modified": "2024-01-02",
                    "publication_date": "2024-01-03",
                    "expiration_date": "2024-01-04",
                    "type": "highlighted",
                    "district": None,
                }
            ]
            result = fetcher.extract()
            self.assertEqual(result, mock_fetch_items_data.return_value)
