from unittest import mock

from django.core.management.base import CommandError
from django.test import SimpleTestCase

from construction_work.management.commands.runetl import Command
from construction_work.models.article_models import Article
from core.utils.dvo_utils import DvORequestError


class RunETLCommandTestCase(SimpleTestCase):
    def test_first_run_skips_notifications_and_garbage_collection(self):
        with (
            mock.patch(
                "construction_work.management.commands.runetl.extract_transform_load",
                return_value=([10], [20]),
            ) as extract,
            mock.patch(
                "construction_work.management.commands.runetl.send_article_notifications"
            ) as send_notifications,
            mock.patch(
                "construction_work.management.commands.runetl.garbage_collector"
            ) as garbage_collector,
        ):
            Command().handle(first_run=True)

        extract.assert_called_once_with()
        send_notifications.assert_not_called()
        garbage_collector.assert_not_called()

    def test_regular_run_sends_notifications_and_collects_garbage(self):
        with (
            mock.patch.object(Article.objects, "values_list", return_value=[10]),
            mock.patch(
                "construction_work.management.commands.runetl.extract_transform_load",
                return_value=([20], [30]),
            ) as extract,
            mock.patch(
                "construction_work.management.commands.runetl.send_article_notifications"
            ) as send_notifications,
            mock.patch(
                "construction_work.management.commands.runetl.garbage_collector"
            ) as garbage_collector,
        ):
            Command().handle()

        extract.assert_called_once_with()
        send_notifications.assert_called_once_with({10}, [30])
        garbage_collector.assert_called_once_with([20], [30])

    @mock.patch(
        "construction_work.management.commands.runetl.extract_transform_load",
        side_effect=DvORequestError("connection refused"),
    )
    def test_dvo_request_failure_aborts_without_traceback(self, _mock_extract):
        with self.assertRaisesMessage(
            CommandError,
            "ETL aborted before data was changed because a DvO request failed: "
            "connection refused",
        ):
            Command().handle(first_run=True)
