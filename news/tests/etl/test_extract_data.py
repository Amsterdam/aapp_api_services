from aioresponses import aioresponses
from django.test import TestCase

from news.etl.extract_data import IproxNewsFetcher
from news.tests.mock_data import all_news, highlighted, item_article, liveblogs


class ExtractDataTest(TestCase):
    def setUp(self):
        self.fetch_url = "https://api.example.com/fetch"
        self.detail_url = "https://api.example.com/detail"

    def test_invalid_initialization(self):
        with self.assertRaises(ValueError):
            IproxNewsFetcher(
                iprox_fetch_url="", iprox_detail_url=self.detail_url, sources=[]
            )

    def test_invalid_sources_configuration(self):
        with self.assertRaises(ValueError):
            IproxNewsFetcher(
                iprox_fetch_url=self.fetch_url,
                iprox_detail_url=self.detail_url,
                sources="not a list",
            )
        with self.assertRaises(ValueError):
            IproxNewsFetcher(
                iprox_fetch_url=self.fetch_url,
                iprox_detail_url=self.detail_url,
                sources=[{"index": "highlighted"}],  # missing boolean_column
            )

    def test_fetch_all_items(self):
        sources = [
            {
                "index": "highlighted",
                "boolean_column": "is_highlight",
                "district": None,
            },
            {
                "index": "liveblogs",
                "boolean_column": "is_liveblog",
                "district": None,
            },
        ]
        fetcher = IproxNewsFetcher(self.fetch_url, self.detail_url, sources=sources)

        with aioresponses() as mocked:
            mocked.get(
                f"{self.fetch_url}/highlighted?page=0",
                payload=highlighted.MOCK_RESPONSE,
            )
            mocked.get(
                f"{self.fetch_url}/liveblogs?page=0", payload=liveblogs.MOCK_RESPONSE
            )
            items = fetcher.fetch_all_items()
            self.assertIsInstance(items, dict)
            self.assertIn(123124, items)
            self.assertIn(1321235, items)
            self.assertTrue(items[123124]["is_highlight"])
            self.assertTrue(items[1321235]["is_liveblog"])

    def test_fetch_all_items_duplicate_ids(self):
        sources = [
            {
                "index": "all_news",
                "boolean_column": "in_all_news",
                "district": None,
            },
            {
                "index": "liveblogs",
                "boolean_column": "is_liveblog",
                "district": None,
            },
        ]
        fetcher = IproxNewsFetcher(self.fetch_url, self.detail_url, sources=sources)

        with aioresponses() as mocked:
            mocked.get(
                f"{self.fetch_url}/all_news?page=0",
                payload=all_news.MOCK_RESPONSE,
            )
            mocked.get(
                f"{self.fetch_url}/liveblogs?page=0", payload=liveblogs.MOCK_RESPONSE
            )
            items = fetcher.fetch_all_items()
            self.assertIsInstance(items, dict)
            self.assertIn(1541234, items)
            self.assertIn(1321235, items)
            self.assertTrue(items[1541234]["in_all_news"])
            self.assertTrue(items[1321235]["in_all_news"])
            self.assertTrue(items[1321235]["is_liveblog"])
            self.assertTrue(items[1234123]["is_liveblog"])

    def test_fetch_items_details(self):
        sources = [
            {
                "index": "highlighted",
                "boolean_column": "is_highlight",
                "district": None,
            }
        ]
        fetcher = IproxNewsFetcher(self.fetch_url, self.detail_url, sources=sources)
        # Prepare items dict
        items = {
            123123: {"id": 123123, "is_highlight": True, "district": None},
            123124: {"id": 123124, "is_highlight": True, "district": None},
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
            self.assertTrue(result[0]["is_highlight"])
            self.assertEqual(result[0]["district"], None)
            self.assertEqual(
                result[1]["title"], item_article.MOCK_RESPONSE_123124["title"]
            )
            self.assertTrue(result[1]["is_highlight"])
            self.assertEqual(result[1]["district"], None)

    def test_extract(self):
        """Test the full extract process, including fetching all items and their details"""
        sources = [
            {
                "index": "highlighted",
                "boolean_column": "is_highlight",
                "district": None,
            },
        ]
        fetcher = IproxNewsFetcher(self.fetch_url, self.detail_url, sources=sources)

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

    def test_combine_detailed_and_basic_info(self):
        """
        Test the combination of detailed and basic information into a single dictionary.
        It is key that the flags of the basic info are preserved, as this is used to store in the database.
        """
        fetcher = IproxNewsFetcher(self.fetch_url, self.detail_url, sources=[])
        basic_info = {
            "id": 123123,
            "district": None,
            "in_all_news": True,
            "is_highlight": True,
            "is_liveblog": False,
            "is_district": False,
        }
        detailed_info = {
            "id": 123123,
            "title": "Test Article",
            "body": "Lorem ipsum",
        }
        combined = fetcher._combine_detailed_and_basic_info(detailed_info, basic_info)
        self.assertEqual(combined["id"], 123123)
        self.assertEqual(combined["district"], None)
        self.assertTrue(combined["in_all_news"])
        self.assertTrue(combined["is_highlight"])
        self.assertFalse(combined["is_liveblog"])
        self.assertEqual(combined["title"], "Test Article")
        self.assertEqual(combined["body"], "Lorem ipsum")
