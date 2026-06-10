import logging
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

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
        ).values_list("foreign_id", "liveblog_version")

        if not active_liveblogs:
            return

        logger.info(
            f"Found {len(active_liveblogs)} active liveblogs. Checking for updates..."
        )

        for foreign_id, liveblog_version in active_liveblogs:
            # Step 2: Check if there are updates for the active liveblogs by comparing the latest version from the Iprox API with the version stored in the database.
            liveblog_version_url = urljoin(
                IPROX_DETAIL_URL, f"{foreign_id}/latest-version"
            )
            try:
                response = self._make_request(liveblog_version_url)
            except requests.exceptions.RequestException:
                logger.error(
                    "Failed to fetch latest version for liveblog.",
                    extra={"foreign_id": foreign_id},
                )
                continue

            latest_version = response.json().get("Vrs")
            if latest_version is None:
                logger.error(
                    "Latest version not found in response for liveblog.",
                    extra={"foreign_id": foreign_id},
                )
                continue

            # check if latest version can be cast to int, if not log error and continue with next liveblog
            try:
                latest_version = int(latest_version)
            except ValueError:
                logger.error(
                    "Latest version is not a valid integer for liveblog.",
                    extra={"foreign_id": foreign_id, "latest_version": latest_version},
                )
                continue

            current_version = liveblog_version if liveblog_version is not None else -1

            if latest_version <= current_version:
                logger.info(
                    "No new updates for liveblog.",
                    extra={
                        "foreign_id": foreign_id,
                        "current_version": current_version,
                        "latest_version": latest_version,
                    },
                )
                continue

            # Step 3: If there are updates, fetch the latest data for the liveblog from the Iprox API
            logger.info(
                "Updates found for liveblog. Transforming and loading data...",
                extra={"foreign_id": foreign_id},
            )
            liveblog_latest_version_url = urljoin(
                IPROX_DETAIL_URL, f"{foreign_id}/retrieve-version/{latest_version}"
            )
            try:
                response = self._make_request(liveblog_latest_version_url)
            except requests.exceptions.RequestException:
                logger.error(
                    "Failed to fetch latest version data for liveblog.",
                    extra={"foreign_id": foreign_id},
                )
                continue

            # Step 4: Transform the data to match the format of our database models.
            transformed_data = transform(
                [
                    {
                        **response.json(),
                        "is_liveblog": True,
                        "district": None,
                    }
                ]
            )

            if not transformed_data:
                logger.error(
                    "Failed to transform data for liveblog.",
                    extra={"foreign_id": foreign_id},
                )
                continue

            # Step 5: Load the transformed data into the database, updating existing records and creating new ones as necessary.
            # When creating new liveblog items, also check if there are notifications for the liveblog and send an update notification if there are.
            data_loader.load(transformed_data)

            # Step 6: Update the liveblog version in the database
            NewsArticle.objects.filter(foreign_id=foreign_id).update(
                liveblog_version=latest_version
            )

            logger.info(
                "Liveblog updated.",
                extra={"foreign_id": foreign_id, "latest_version": latest_version},
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,  # Reraise the RequestException after retries
    )
    def _make_request(self, url) -> requests.Response:
        """Make the HTTP request for with retries and a timeout."""
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response
