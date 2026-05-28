import logging
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from news.etl.load_data import NewsArticleLoader
from news.etl.transform_data import transform
from news.models import NewsArticle

logger = logging.getLogger(__name__)

data_loader = NewsArticleLoader()

IPROX_URL = urljoin(settings.IPROX_SERVER, "appidt/news/")
IPROX_DETAIL_URL = urljoin(IPROX_URL, "item/")


class Command(BaseCommand):
    """
    This command is responsible for checking for updates in active liveblogs.

    The command performs the following steps:
    1. Check if there are any active liveblogs in the database.
    2. Check if there are updates for the active liveblogs by comparing the latest version from the Iprox API with the version stored in the database.
    3. If there are updates, fetch the latest data for the liveblog from the Iprox API.
    4. Transform the data to match the format of our database models.
    5. Load the transformed data into the database, updating existing records and creating new ones as necessary.
    6. Send notifications if there is a new update for the liveblog.
    """

    help = "Check for updates in active liveblogs"

    def handle(self, *args, **kwargs):

        logger.info("Starting liveblog update process...")

        # Step 1: Check if there are any active liveblogs in the database.
        active_liveblogs = NewsArticle.objects.filter(
            type="liveblog",
            is_active_liveblog=True,
        ).values_list("foreign_id", "liveblog_version", flat=True)

        if not active_liveblogs:
            logger.info("No active liveblogs found. Exiting.")
            return

        logger.info(
            f"Found {len(active_liveblogs)} active liveblogs. Checking for updates..."
        )

        for foreign_id, liveblog_version in active_liveblogs:
            logger.info(
                f"Checking liveblog with foreign_id {foreign_id} and version {liveblog_version}..."
            )

            # Step 2: Check if there are updates for the liveblog by comparing the latest version from the Iprox API with the version stored in the database.
            liveblog_version_url = urljoin(
                IPROX_DETAIL_URL, f"/{foreign_id}/latest-version"
            )
            response = requests.get(liveblog_version_url)
            if response.status_code != 200:
                logger.error(
                    f"Failed to fetch latest version for liveblog {foreign_id}. Status code: {response.status_code}"
                )
                continue
            latest_version = response.json().get("Vrs")
            if latest_version is None:
                logger.error(
                    f"Latest version not found in response for liveblog {foreign_id}. Response: {response.text}"
                )
                continue

            if int(latest_version) <= liveblog_version:
                logger.info(
                    f"No new updates for liveblog {foreign_id}. Current version: {liveblog_version}, Latest version: {latest_version}"
                )
                continue

            # Step 3: If there are updates, fetch the latest data for the liveblog.
            logger.info(
                f"Updates found for liveblog {foreign_id}. Transforming and loading data..."
            )
            liveblog_latest_version_url = urljoin(
                IPROX_DETAIL_URL, f"/{foreign_id}/retrieve-version/{latest_version}"
            )
            response = requests.get(liveblog_latest_version_url)
            if response.status_code != 200:
                logger.error(
                    f"Failed to fetch latest version for liveblog {foreign_id}. Status code: {response.status_code}"
                )
                continue

            transformed_data = transform([response.json()])
            data_loader.load(transformed_data)

            logger.info(f"Liveblog {foreign_id} updated to version {latest_version}.")
