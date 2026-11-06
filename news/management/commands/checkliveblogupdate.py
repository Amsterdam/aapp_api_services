import asyncio
import logging

import aiohttp
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from core.utils.dvo_utils import DvOClient, DvOResponseError
from news.etl.load_data import NewsArticleLoader
from news.etl.queries import blog_base_info, blog_full_content
from news.etl.transform_data import transform
from news.models import NewsArticle

logger = logging.getLogger(__name__)

data_loader = NewsArticleLoader()


class Command(BaseCommand):
    """
    This command is responsible for checking for updates in active liveblogs.

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

    def handle(self, *args, **kwargs):

        logger.info("Starting liveblog update process...")

        # Step 1: Check if there are any active liveblogs in the database.
        active_liveblogs = NewsArticle.objects.filter(
            is_liveblog=True,
            is_active_liveblog=True,
            deleted=False,
        )

        if not active_liveblogs:
            return

        logger.info(
            f"Found {len(active_liveblogs)} active liveblogs. Checking for updates..."
        )

        for liveblog in active_liveblogs:
            foreign_id = liveblog.foreign_id

            # Step 2: check if the liveblog has updates based on the changedDate from the API
            try:
                has_update = self.liveblog_has_update(liveblog)
            except (
                aiohttp.ClientError,
                asyncio.TimeoutError,
                DvOResponseError,
            ):
                logger.exception(
                    "Failed to check for liveblog updates.",
                    extra={"foreign_id": foreign_id},
                )
                continue

            if not has_update:
                logger.info(
                    "No new updates for liveblog based on changedDate.",
                    extra={"foreign_id": foreign_id},
                )
                continue

            # Step 3: If there are updates, fetch the latest data for the liveblog from the Iprox API
            logger.info(
                "Updates found for liveblog. Transforming and loading data...",
                extra={"foreign_id": foreign_id},
            )

            try:
                full_blog = self.fetch_full_blog_information(foreign_id)
            except (
                aiohttp.ClientError,
                asyncio.TimeoutError,
                DvOResponseError,
            ):
                logger.exception(
                    "Failed to fetch liveblog updates.",
                    extra={"foreign_id": foreign_id},
                )
                continue

            if not full_blog:
                logger.error(
                    "Failed to fetch full blog information for liveblog.",
                    extra={"foreign_id": foreign_id},
                )
                continue

            # Step 4: Transform the data to match the format of our database models.
            transformed_data = transform([full_blog])

            if not transformed_data:
                logger.error(
                    "Failed to transform data for liveblog.",
                    extra={"foreign_id": foreign_id},
                )
                continue

            # Step 5: Load the transformed data into the database, updating existing records and creating new ones as necessary.
            # When creating new liveblog items, also check if there are notifications for the liveblog and send an update notification if there are.
            data_loader.load(transformed_data)

            logger.info(
                "Liveblog updated.",
                extra={"foreign_id": foreign_id},
            )

    def liveblog_has_update(self, liveblog):
        """Get blog info for the liveblog."""
        blog_info = asyncio.run(
            self._run_query(blog_base_info.QUERY, liveblog.foreign_id)
        )
        new_changed_date = (blog_info.get("nodeByID") or {}).get("changedDate")
        if not new_changed_date:
            return False

        if not isinstance(new_changed_date, str):
            logger.error(
                "Invalid changed date for liveblog.",
                extra={"foreign_id": liveblog.foreign_id},
            )
            return False

        new_changed_datetime = parse_datetime(new_changed_date)
        if new_changed_datetime is None:
            logger.error(
                "Invalid changed date for liveblog.",
                extra={
                    "foreign_id": liveblog.foreign_id,
                    "changed_date": new_changed_date,
                },
            )
            return False

        if timezone.is_naive(new_changed_datetime):
            new_changed_datetime = timezone.make_aware(
                new_changed_datetime, timezone.get_default_timezone()
            )

        old_changed_date = liveblog.modification_datetime
        if not old_changed_date:
            return True

        return new_changed_datetime > old_changed_date

    def fetch_full_blog_information(self, foreign_id):
        blog_content = asyncio.run(self._run_query(blog_full_content.QUERY, foreign_id))
        return blog_content.get("nodeByID")

    async def _run_query(self, query, foreign_id):
        async with DvOClient() as client:
            return await client.execute_query(
                query,
                {"nodeID": foreign_id},
            )
