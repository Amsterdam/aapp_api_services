""" Fetch all project and article data from IPROX via its API
    See README.md for more info regarding the IPROX API
"""
import asyncio
from datetime import datetime
from urllib.parse import urljoin

import aiohttp
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from django.conf import settings

from logging import getLogger
logger = getLogger(__name__)


class FetchError(Exception):
    pass


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
    upsert_item_data = [item for item in upsert_item_data if item]  # Take out None values
    logger.info(f"Finished async fetch. Successfully collected {len(upsert_item_data)} items")
    return upsert_item_data


async def async_fetch(urls, max_concurrent_requests=20):
    """Fetch all URLs with limited concurrency. 20 seems to be the sweet spot."""
    sem = asyncio.Semaphore(max_concurrent_requests)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_with_sem(sem, session, url) for url in urls]
        return await asyncio.gather(*tasks)


async def fetch_with_sem(sem, session, url):
    """Fetch a URL, respecting the semaphore limit."""
    async with sem:
        try:
            return await fetch(session, url)
        except:
            logger.error(f"Failed to fetch {url}")


@retry(
    stop=stop_after_attempt(3),  # Retry up to 3 times
    wait=wait_fixed(2),          # Wait 2 seconds between retries
    retry=retry_if_exception_type(FetchError)  # Retry only on custom exceptions
)
async def fetch(session, url):
    """Fetch a single URL with a retry mechanism."""
    try:
        async with session.get(url) as response:
            if response.status != 200:
                raise FetchError(f"Failed to fetch {url}, status code: {response.status}")
            return await response.json()
    except aiohttp.ClientError as e:
        raise FetchError(f"Failed to fetch {url}: {str(e)}") from e
