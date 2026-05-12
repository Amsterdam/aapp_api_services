from aioresponses import aioresponses
from django.test import TestCase

from news.etl.extract_data import IproxFetcher
from news.tests.mock_data import highlighted, item_article, liveblogs


class ExtractDataTest(TestCase):
    def setUp(self):
        self.fetch_url = "https://api.example.com/fetch"
        self.detail_url = "https://api.example.com/detail"

    def test_fetch_all_items(self):
        sources = [
            {"index": "highlighted", "type": "highlighted", "district": None},
            {"index": "liveblogs", "type": "liveblog", "district": None},
        ]
        fetcher = IproxFetcher(self.fetch_url, self.detail_url, sources=sources)

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

    def test_fetch_items_details(self):
        sources = [{"index": "highlighted", "type": "highlighted", "district": None}]
        fetcher = IproxFetcher(self.fetch_url, self.detail_url, sources=sources)
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

            result = fetcher.fetch_items_details(items)
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

    def test_extract(self):
        """Test the full extract process, including fetching all items and their details"""
        sources = [
            {"index": "highlighted", "type": "highlighted", "district": None},
        ]
        fetcher = IproxFetcher(self.fetch_url, self.detail_url, sources=sources)

        with aioresponses() as mocked:
            # Mock fetching all items
            mocked.get(
                f"{self.fetch_url}/highlighted?page=0",
                payload=highlighted.MOCK_RESPONSE,
            )
            # Mock fetching item details
            mocked.get(
                f"{self.detail_url}/123123", payload=item_article.MOCK_RESPONSE_123123
            )
            mocked.get(
                f"{self.detail_url}/123124", payload=item_article.MOCK_RESPONSE_123124
            )

            extracted_data = fetcher.extract()
            self.assertEqual(len(extracted_data), 2)
