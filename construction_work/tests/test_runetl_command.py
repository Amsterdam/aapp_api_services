from unittest import mock

from django.core.management.base import CommandError
from django.test import SimpleTestCase

from construction_work.management.commands.runetl import Command
from core.utils.dvo_utils import DvORequestError


class RunETLCommandTestCase(SimpleTestCase):
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
