from unittest.mock import call, patch

from django.core.management import call_command
from django.test import TestCase

from news.management.commands import runconstructionworketl
from news.models.article_models import NewsArticle
from news.models.project_models import Project


class RunConstructionWorkETLTest(TestCase):
    def _projects_payload(self):
        return [
            {
                "id": 7001,
                "title": "Bridge maintenance",
                "subtitle": "Keep traffic moving",
                "url": "https://example.com/projects/7001",
                "created": "2024-01-01T12:00:00Z",
                "modified": "2024-01-02T12:00:00Z",
                "expirationDate": None,
                "timeline": {"title": "Timeline", "intro": "Intro", "items": []},
                "coordinates": {"lat": 52.37, "lon": 4.89},
                "sections": {
                    "where": [
                        {
                            "title": "Where",
                            "body": "In Centrum",
                            "links": [],
                        }
                    ],
                    "what": [],
                    "when": [],
                    "work": [],
                    "contact": [],
                },
                "contacts": [],
                "image_url": "",
            }
        ]

    def _articles_payload(self):
        return [
            {
                "id": 8001,
                "title": "<div>Construction update</div>",
                "body": "<div><p>Road closed.</p></div>",
                "summary": "<div><p>Summary.</p></div>",
                "intro": "<div><p>Intro.</p></div>",
                "district": None,
                "url": "https://example.com/news/8001",
                "created": "2024-01-01T12:00:00Z",
                "modified": "2024-01-01T13:00:00Z",
                "publicationDate": "2024-01-01T13:00:00Z",
                "image_url": "",
                "is_construction_work": True,
            }
        ]

    @patch("news.management.commands.runconstructionworketl.iprox_fetcher.extract")
    def test_run_construction_work_etl_persists_projects_and_articles(
        self, mock_extract
    ):
        mock_extract.side_effect = [self._projects_payload(), self._articles_payload()]

        call_command("runconstructionworketl")

        self.assertTrue(Project.objects.filter(foreign_id=7001).exists())
        article = NewsArticle.objects.get(foreign_id=8001)
        self.assertTrue(article.is_construction_work)

    @patch("news.management.commands.runconstructionworketl.logger.info")
    @patch("news.management.commands.runconstructionworketl.logger.error")
    @patch("news.management.commands.runconstructionworketl.iprox_fetcher.extract")
    def test_run_construction_work_etl_does_not_log_success_after_no_projects(
        self,
        mock_extract,
        mock_logger_error,
        mock_logger_info,
    ):
        mock_extract.return_value = []

        call_command("runconstructionworketl")

        mock_extract.assert_called_once_with(runconstructionworketl.IPROX_PROJECTS_URL)
        mock_logger_error.assert_called_once()
        self.assertNotIn(
            call("ETL process completed successfully."),
            mock_logger_info.call_args_list,
        )
        self.assertEqual(Project.objects.count(), 0)
        self.assertEqual(NewsArticle.objects.count(), 0)

    @patch("news.management.commands.runconstructionworketl.logger.info")
    @patch("news.management.commands.runconstructionworketl.logger.error")
    @patch("news.management.commands.runconstructionworketl.iprox_fetcher.extract")
    def test_run_construction_work_etl_short_circuits_when_no_articles(
        self,
        mock_extract,
        mock_logger_error,
        mock_logger_info,
    ):
        mock_extract.side_effect = [self._projects_payload(), []]

        call_command("runconstructionworketl")

        self.assertEqual(mock_extract.call_count, 2)
        self.assertTrue(Project.objects.filter(foreign_id=7001).exists())
        self.assertEqual(NewsArticle.objects.count(), 0)
        mock_logger_error.assert_called_once()
        self.assertNotIn(
            call("ETL process completed successfully."),
            mock_logger_info.call_args_list,
        )
