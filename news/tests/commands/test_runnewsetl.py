from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase

from news.management.commands import runnewsetl


class RunNewsETLTest(SimpleTestCase):
    def test_run_news_etl_stops_when_no_articles_are_extracted(self):
        with (
            patch.object(runnewsetl, "get_all_drupal_news", return_value=[]) as extract,
            patch.object(runnewsetl, "transform") as transform,
        ):
            call_command("runnewsetl")

        extract.assert_called_once_with()
        transform.assert_not_called()

    def test_run_news_etl_passes_raw_drupal_nodes_to_transform(self):
        extracted_nodes = [
            {"__typename": "News", "id": 123, "title": "A news article"},
        ]
        with (
            patch.object(
                runnewsetl,
                "get_all_drupal_news",
                return_value=extracted_nodes,
            ) as extract,
            patch.object(runnewsetl, "transform", return_value=[]) as transform,
        ):
            call_command("runnewsetl")

        extract.assert_called_once_with()
        transform.assert_called_once_with(extracted_nodes)
