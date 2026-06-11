import logging
from unittest.mock import patch
from urllib.parse import urljoin

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from news.management.commands import checkliveblogupdate
from news.management.mock_data import liveblogs_item, liveblogs_list

logger = logging.getLogger(__name__)


class MockResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class Command(BaseCommand):
    """
    This command is responsible for mocking updates in active liveblogs.

    The command performs the following steps:
    1. Check if there are any active liveblogs in the database.
    2. Check if there are updates for the active liveblogs by comparing the latest version from the Iprox API with the version stored in the database.
    3. If there are updates, fetch the latest data for the liveblog from the Iprox API.
    4. Transform the data to match the format of our database models.
    5. Load the transformed data into the database, updating existing records and creating new ones as necessary.
       When creating new liveblog items, also check if there are notifications for the liveblog and send an update notification if there are.
    6. Update the liveblog version in the database
    """

    help = "Check for updates in active liveblogs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--liveblog-version",
            action="store",
            default="1",
            help="Sets version of active liveblogs",
        )

    def handle(self, *args, **kwargs):

        # check environment, never run on production
        if settings.ENVIRONMENT == "production":
            logger.error("This command should not be run in production!")
            return

        liveblog_version = str(kwargs.get("liveblog_version", "1"))
        if liveblog_version not in liveblogs_item.MOCK_RESPONSES:
            raise CommandError(
                f"Unsupported --liveblog-version '{liveblog_version}'. "
                f"Available versions: {', '.join(sorted(liveblogs_item.MOCK_RESPONSES.keys()))}."
            )

        # get foreign id of active liveblog
        liveblog_list_mock_response = liveblogs_list.MOCK_RESPONSE
        liveblog_id = liveblog_list_mock_response["items"][0]["id"]

        liveblog_version_url = urljoin(
            checkliveblogupdate.IPROX_DETAIL_URL, f"{liveblog_id}/latest-version"
        )
        liveblog_latest_version_url = urljoin(
            checkliveblogupdate.IPROX_DETAIL_URL,
            f"{liveblog_id}/retrieve-version/{liveblog_version}",
        )

        version_payload = {
            "Vrs": str(liveblog_version),
            "Dtm": "20260508",
            "Tyd": "1006",
        }
        latest_payload = liveblogs_item.MOCK_RESPONSES[str(liveblog_version)]

        def _mock_make_request(url):
            if url == liveblog_version_url:
                return MockResponse(version_payload)
            if url == liveblog_latest_version_url:
                return MockResponse(latest_payload)
            raise CommandError(f"Unexpected URL in mockcheckliveblogupdate: {url}")

        with patch.object(
            checkliveblogupdate.Command,
            "_make_request",
            side_effect=_mock_make_request,
        ):
            call_command("checkliveblogupdate")
