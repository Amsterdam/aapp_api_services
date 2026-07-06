"""Fetch all project and article data from IPROX via its API
See README.md for more info regarding the IPROX API
"""

import asyncio
from datetime import datetime
from logging import getLogger
from urllib.parse import urljoin

from django.conf import settings

from core.utils.async_utils import async_fetch

logger = getLogger(__name__)


def get_all_iprox_items(iprox_url):
    """Get a list of items from the IPROX API asyncronously
    The "modified" field is converted to a datetime object
    """
    logger.info("Collecting list of items")
    result = asyncio.run(async_fetch([iprox_url]))[0]
    if not result:
        return None

    for item in result:
        date_string = item.get("modified", settings.EPOCH)
        item["modified"] = datetime.strptime(date_string, settings.DATE_FORMAT_IPROX)
    return result


def get_iprox_items_data(url, item_ids):
    """Get all data for each item by ID."""
    urls = [urljoin(url, str(item)) for item in item_ids]
    logger.info(f"Starting async fetch for {len(urls)} items from IPROX")
    upsert_item_data = asyncio.run(async_fetch(urls))
    upsert_item_data = [
        item for item in upsert_item_data if item
    ]  # Take out None values
    logger.info(
        f"Finished async fetch. Successfully collected {len(upsert_item_data)} items"
    )
    return upsert_item_data
