from unittest import mock
from unittest.mock import AsyncMock

from django.test import SimpleTestCase, override_settings

from construction_work.etl import extract_data
from construction_work.etl.queries import news_articles, projects_with_details
from core.utils.dvo_utils import DvOResponseError


def project_with_news_view(paragraph_id, **news_view_fields):
    return {
        "content": [
            {
                "rows": [
                    {
                        "content": [
                            None,
                            {
                                "__typename": "ParagraphDdsViews",
                                "id": paragraph_id,
                                **news_view_fields,
                            },
                        ]
                    }
                ]
            }
        ]
    }


class DvoExtractionTestCase(SimpleTestCase):
    def test_extracts_news_paragraph_id_from_content_indication(self):
        project = project_with_news_view(
            123,
            contentIndication="news",
            title="Project updates",
        )

        paragraph_id = extract_data.extract_news_paragraph_id_from_project(project)

        self.assertEqual(paragraph_id, 123)

    def test_extracts_news_paragraph_id_from_legacy_title(self):
        project = project_with_news_view(456, title="Nieuws")

        paragraph_id = extract_data.extract_news_paragraph_id_from_project(project)

        self.assertEqual(paragraph_id, 456)

    def test_returns_none_when_project_has_no_news_view(self):
        project = {"content": [{"rows": [{"content": [None]}]}]}

        paragraph_id = extract_data.extract_news_paragraph_id_from_project(project)

        self.assertIsNone(paragraph_id)

    def test_rejects_news_view_without_integer_id(self):
        project = project_with_news_view("not-an-integer", title="Nieuws")

        with self.assertRaises(DvOResponseError):
            extract_data.extract_news_paragraph_id_from_project(project)

    @override_settings(DVO_CONSTRUCTION_WORK_PARAGRAPH_ID=12345)
    def test_get_all_projects_returns_raw_projects_and_grouped_articles(self):
        projects = [
            project_with_news_view(123, title="Nieuws"),
            project_with_news_view(123, title="Nieuws"),
            project_with_news_view(456, title="Nieuws"),
        ]
        articles_by_paragraph_id = [
            [{"id": 1001, "title": "First article"}],
            [{"id": 1002, "title": "Second article"}],
        ]
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.execute_paginated_view_query.return_value = projects
        client.execute_paginated_view_queries.return_value = articles_by_paragraph_id

        with mock.patch.object(extract_data, "DvOClient", return_value=client):
            extracted_data = extract_data.get_all_drupal_projects_with_content()

        client.execute_paginated_view_query.assert_awaited_once_with(
            projects_with_details.QUERY,
            {"paragraphId": 12345},
        )
        client.execute_paginated_view_queries.assert_awaited_once_with(
            news_articles.QUERY,
            [{"paragraphId": 123}, {"paragraphId": 456}],
        )
        self.assertEqual(extracted_data["projects"], projects)
        self.assertEqual(
            extracted_data["news_articles"],
            {
                123: articles_by_paragraph_id[0],
                456: articles_by_paragraph_id[1],
            },
        )

    def test_news_articles_query_accepts_page_variable(self):
        self.assertIn("$page: Int!", news_articles.QUERY)
        self.assertIn("page: $page", news_articles.QUERY)
