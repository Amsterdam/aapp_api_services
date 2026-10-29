from unittest import mock
from unittest.mock import AsyncMock

from django.test import SimpleTestCase, override_settings

from construction_work.etl import extract_data
from construction_work.etl.queries import (
    news_articles as news_articles_query,
)
from construction_work.etl.queries import (
    projects_with_details,
)
from construction_work.etl.queries import (
    work_articles as work_articles_query,
)
from construction_work.tests.mock_data.source.articles import (
    news_article_view,
    work_article_view,
)
from construction_work.tests.mock_data.source.projects import (
    project_with_news_view,
    project_with_work_view,
    projects_overview,
)
from core.utils.dvo_utils import DvOResponseError


class ExtractDataTestCase(SimpleTestCase):
    @override_settings(DVO_CONSTRUCTION_WORK_PARAGRAPH_ID=12345)
    def test_get_all_projects_returns_raw_projects_and_grouped_articles(self):
        projects_mock_data = projects_overview.MOCK_RESPONSE["data"]["view"]["nodes"]
        news_articles_by_paragraph_id = [
            news_article_view.MOCK_RESPONSE_79631["data"]["view"]["nodes"],
            news_article_view.MOCK_RESPONSE_79932["data"]["view"]["nodes"],
            news_article_view.MOCK_RESPONSE_79592["data"]["view"]["nodes"],
        ]
        work_articles_by_paragraph_id = [
            work_article_view.MOCK_RESPONSE["data"]["view"]["nodes"]
        ]

        client = AsyncMock()
        client.__aenter__.return_value = client
        client.execute_paginated_view_query.return_value = projects_mock_data
        client.execute_paginated_view_queries.side_effect = [
            news_articles_by_paragraph_id,
            work_articles_by_paragraph_id,
        ]

        with mock.patch.object(extract_data, "DvOClient", return_value=client):
            extracted_data = extract_data.get_all_drupal_projects_with_content()

        client.execute_paginated_view_query.assert_awaited_once_with(
            projects_with_details.QUERY,
            {"paragraphId": 12345},
        )
        self.assertEqual(
            client.execute_paginated_view_queries.await_args_list,
            [
                mock.call(
                    news_articles_query.QUERY,
                    [
                        {"paragraphId": 79631},
                        {"paragraphId": 79932},
                        {"paragraphId": 79592},
                    ],
                ),
                mock.call(
                    work_articles_query.QUERY,
                    [{"paragraphId": 79593}],
                ),
            ],
        )
        self.assertEqual(extracted_data["projects"], projects_mock_data)
        self.assertEqual(
            extracted_data["news_articles"],
            {
                79631: news_articles_by_paragraph_id[0],
                79932: news_articles_by_paragraph_id[1],
                79592: news_articles_by_paragraph_id[2],
            },
        )
        self.assertEqual(
            extracted_data["work_articles"],
            {79593: work_articles_by_paragraph_id[0]},
        )

    def test_extracts_news_paragraph_id(self):
        paragraph_id_dict = (
            extract_data.extract_news_and_work_paragraph_id_from_project(
                project_with_news_view.MOCK_DATA
            )
        )

        self.assertEqual(paragraph_id_dict, [{"paragraph_id": 79631, "type": "news"}])

    def test_extracts_both_news_and_work_paragraph_ids(self):
        paragraph_ids = extract_data.extract_news_and_work_paragraph_id_from_project(
            project_with_work_view.MOCK_DATA
        )

        self.assertEqual(
            paragraph_ids,
            [
                {"paragraph_id": 79592, "type": "news"},
                {"paragraph_id": 79593, "type": "work"},
            ],
        )

    def test_extracts_work_paragraph_id(self):
        project = {
            "content": [
                {
                    "rows": [
                        {
                            "content": [
                                {
                                    "__typename": "ParagraphDdsViews",
                                    "id": 456,
                                    "contentIndication": "work",
                                    "title": "Werk aan de weg",
                                },
                            ]
                        }
                    ]
                }
            ]
        }

        paragraph_ids = extract_data.extract_news_and_work_paragraph_id_from_project(
            project
        )

        self.assertEqual(
            paragraph_ids,
            [
                {"paragraph_id": 456, "type": "work"},
            ],
        )

    def test_skips_non_mapping_content_structure(self):
        project = {
            "content": [
                None,
                "not a grid",
                {
                    "rows": [
                        None,
                        {"content": [None, "not a block"]},
                    ]
                },
            ]
        }

        self.assertEqual(
            extract_data.extract_news_and_work_paragraph_id_from_project(project),
            [],
        )

    def test_rejects_view_blocks_with_non_integer_ids(self):
        for content_indication, title in (
            ("news", "Nieuws"),
            ("work", "Werk aan de weg"),
        ):
            with self.subTest(content_indication=content_indication):
                project = {
                    "content": [
                        {
                            "rows": [
                                {
                                    "content": [
                                        {
                                            "__typename": "ParagraphDdsViews",
                                            "id": True,
                                            "contentIndication": content_indication,
                                            "title": title,
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }

                with self.assertRaises(DvOResponseError):
                    extract_data.extract_news_and_work_paragraph_id_from_project(
                        project
                    )

    def test_news_articles_query_accepts_page_variable(self):
        self.assertIn("$page: Int!", news_articles_query.QUERY)
        self.assertIn("page: $page", news_articles_query.QUERY)
