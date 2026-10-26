from unittest import mock
from unittest.mock import AsyncMock

from django.test import SimpleTestCase, override_settings

from news.etl import extract_data
from news.etl.queries import news_blogs_with_content
from news.tests.mock_data import all_news


class DvoNewsExtractionTestCase(SimpleTestCase):
    @override_settings(DVO_NEWS_PARAGRAPH_ID=12345)
    def test_get_all_drupal_news_returns_paginated_view_nodes(self):
        nodes = all_news.MOCK_RESPONSE["data"]["view"]["nodes"]
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.execute_paginated_view_query.return_value = nodes

        with mock.patch.object(extract_data, "DvOClient", return_value=client):
            extracted_data = extract_data.get_all_drupal_news()

        client.execute_paginated_view_query.assert_awaited_once_with(
            news_blogs_with_content.QUERY,
            {"paragraphId": 12345},
        )
        self.assertEqual(extracted_data, nodes)

    def test_news_blogs_query_accepts_paragraph_and_page_variables(self):
        self.assertIn("$paragraphId: Int!", news_blogs_with_content.QUERY)
        self.assertIn("$page: Int!", news_blogs_with_content.QUERY)
        self.assertIn("page: $page", news_blogs_with_content.QUERY)
