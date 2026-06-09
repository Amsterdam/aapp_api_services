import logging
from unittest.mock import patch
from urllib.parse import urljoin

from aioresponses import aioresponses
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from news.management.commands import runnewsetl
from news.management.mock_data import (
    highlighted_item,
    highlighted_list,
    liveblogs_item,
    liveblogs_list,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Mock run news ETL process.

    We use mock data.
    """

    help = "Mock run news ETL process"

    def handle(self, *args, **kwargs):

        # check environment, never run on production
        if settings.ENVIRONMENT == "production":
            logger.error("This command should not be run in production!")
            return

        # define the urls and ids we need for the mocked responses
        LIVEBLOG_LIST_MOCK_RESPONSE = liveblogs_list.MOCK_RESPONSE
        liveblog_id = LIVEBLOG_LIST_MOCK_RESPONSE["items"][0]["id"]

        HIGHLIGHTED_LIST_MOCK_RESPONSE = highlighted_list.MOCK_RESPONSE
        highlighted_id = HIGHLIGHTED_LIST_MOCK_RESPONSE["items"][1]["id"]

        liveblogs_url = f"{urljoin(runnewsetl.IPROX_ARTICLES_URL, 'liveblogs')}?page=0"
        liveblog_detail_url = urljoin(runnewsetl.IPROX_DETAIL_URL, str(liveblog_id))
        highlighted_url = (
            f"{urljoin(runnewsetl.IPROX_ARTICLES_URL, 'highlighted')}?page=0"
        )
        highlighted_detail_url = urljoin(
            runnewsetl.IPROX_DETAIL_URL, str(highlighted_id)
        )

        # Patch the fetcher instance used by runnewsetl so only mocked sources are fetched.
        mocked_sources = [
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
        # As we want the liveblog to show up in the highlights, we also need to mock the highlights endpoint.
        # There is also one other highlighted article, so we see that the rotation in the frontend stops
        with patch.object(runnewsetl.iprox_fetcher, "sources", mocked_sources):
            with aioresponses() as mocked:
                mocked.get(liveblogs_url, payload=LIVEBLOG_LIST_MOCK_RESPONSE)
                mocked.get(
                    liveblog_detail_url, payload=liveblogs_item.MOCK_RESPONSES["1"]
                )
                mocked.get(highlighted_url, payload=HIGHLIGHTED_LIST_MOCK_RESPONSE)
                mocked.get(
                    highlighted_detail_url, payload=highlighted_item.MOCK_RESPONSE
                )
                call_command("runnewsetl")
