import logging
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

        LIVEBLOG_LIST_MOCK_RESPONSE = liveblogs_list.MOCK_RESPONSE
        liveblog_id = LIVEBLOG_LIST_MOCK_RESPONSE["items"][0]["id"]

        HIGHLIGHTED_LIST_MOCK_RESPONSE = highlighted_list.MOCK_RESPONSE
        highlighted_id = HIGHLIGHTED_LIST_MOCK_RESPONSE["items"][1]["id"]

        liveblogs_url = f"{urljoin(runnewsetl.IPROX_ARTICLES_URL, 'liveblogs')}?page=0"
        liveblog_detail_url = urljoin(runnewsetl.IPROX_DETAIL_URL, str(liveblog_id))
        highlights_url = (
            f"{urljoin(runnewsetl.IPROX_ARTICLES_URL, 'highlighted')}?page=0"
        )
        highlighted_detail_url = urljoin(
            runnewsetl.IPROX_DETAIL_URL, str(highlighted_id)
        )

        # as we want the liveblog to show up in the higlights, we also need to mock the highlights endpoint.
        # There is also one other hightlighted article, so we see that the roulation in the frontend stops
        with aioresponses(passthrough_unmatched=True) as mocked:
            mocked.get(liveblogs_url, payload=LIVEBLOG_LIST_MOCK_RESPONSE)
            mocked.get(liveblog_detail_url, payload=liveblogs_item.MOCK_RESPONSES["1"])
            mocked.get(highlights_url, payload=highlighted_list.MOCK_RESPONSE)
            mocked.get(highlighted_detail_url, payload=highlighted_item.MOCK_RESPONSE)
            call_command("runnewsetl")
