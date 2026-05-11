import asyncio
import logging
from datetime import datetime
from urllib.parse import urljoin

import aiohttp
from django.conf import settings
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from news.models import NewsArticle

logger = logging.getLogger(__name__)


class FetchError(Exception):
    pass


class IproxFetcher:
    def __init__(
        self,
        iprox_fetch_url: str,
        iprox_detail_url: str,
        sources: list[dict] | None = None,
        max_concurrent_requests: int = 20,
        is_paginated: bool = False,
    ):
        """Initialize the fetcher with URLs and settings.
        Args:
            iprox_fetch_url (str): The URL to fetch the list of items.
            iprox_detail_url (str): The URL to fetch item details.
            sources (list[dict] | None): Optional list of sources to fetch from.
            max_concurrent_requests (int): Maximum number of concurrent requests.
            is_paginated (bool): Whether the API is paginated. This determines if
                the fetch_all_items method needs to handle pagination and if the
                response is a list (non-paginated) or a dict with a "items" key (paginated).
        """
        # check that urls are defined, otherwise raise an error
        if not iprox_fetch_url or not iprox_detail_url:
            raise ValueError(
                "Both iprox_fetch_url and iprox_detail_url must be provided"
            )
        self.iprox_fetch_url = iprox_fetch_url
        self.iprox_detail_url = iprox_detail_url
        self.sources = sources
        self.max_concurrent_requests = max_concurrent_requests
        self.is_paginated = is_paginated

    def extract(self) -> list[dict]:
        # Step 1: Extract base info for all items
        logger.info("Extracting base info for all news articles from source")
        all_iprox_items = self.fetch_all_items()  # dict: id -> base info

        # Step 2: Query DB for existing articles (fetch only needed fields)
        db_articles = {
            a["foreign_id"]: a
            for a in NewsArticle.objects.values(
                "foreign_id",
                "creation_date",
                "modification_date",
                "publication_date",
                "expiration_date",
                "type",
                "district",
            )
        }

        # Step 3: Determine new and altered items
        new_or_altered = {
            item_id: item
            for item_id, item in all_iprox_items.items()
            if (db_item := db_articles.get(item_id)) is None
            or self.is_altered(db_item, item)
        }

        if not new_or_altered:
            return None

        # Step 4: Fetch details only for new/altered items
        logger.info(
            f"Found {len(new_or_altered)} new or altered news articles to update."
        )
        extracted_data = self.fetch_items_data(items=new_or_altered)
        logger.info(f"Extracted {len(extracted_data)} news articles from source")
        return extracted_data

    def fetch_all_items(self) -> dict:
        """Get a list of items from the IPROX API."""
        all_items = {}
        if self.sources is None:
            result = asyncio.run(self._async_fetch([self.iprox_fetch_url]))[0]
            for item in result:
                date_string = item.get("modified", settings.EPOCH)
                item["modified"] = datetime.strptime(
                    date_string, settings.DATE_FORMAT_IPROX
                )
                item["type"] = None
                item["district"] = None
                all_items[item["id"]] = item
            return all_items

        for source in self.sources:
            logger.info(f"Collecting list of items for source {source}")
            source_url = urljoin(self.iprox_fetch_url, source["index"])
            if self.is_paginated:
                # If the API is paginated, we need to fetch all pages
                page = 0
                while True:
                    paginated_url = f"{source_url}?page={page}"
                    result = asyncio.run(self._async_fetch([paginated_url]))
                    items = result.get("items", [])
                    for item in items:
                        date_string = item.get("modified", settings.EPOCH)
                        item["modified"] = datetime.strptime(
                            date_string, settings.DATE_FORMAT_IPROX
                        )
                        item["type"] = source["type"]
                        item["district"] = source.get("district")
                        if item["id"] in all_items:
                            logger.warning(
                                f"Duplicate item ID {item['id']} found. Old type: {all_items[item['id']]['type']}, new type: {source['type']}. Overwriting previous item."
                            )
                        all_items[item["id"]] = item
                    pages = result.get("pages", 1)
                    if page == pages - 1:
                        break
                    page += 1
            else:
                result = asyncio.run(self._async_fetch([source_url]))[0]
                if not result:
                    return None
                for item in result:
                    date_string = item.get("modified", settings.EPOCH)
                    item["modified"] = datetime.strptime(
                        date_string, settings.DATE_FORMAT_IPROX
                    )
                    item["type"] = source["type"]
                    item["district"] = source.get("district")
                    if item["id"] in all_items:
                        logger.warning(
                            f"Duplicate item ID {item['id']} found. Old type: {all_items[item['id']]['type']}, new type: {source['type']}. Overwriting previous item."
                        )
                    all_items[item["id"]] = item
        return all_items

    @staticmethod
    def is_altered(db_item: NewsArticle, item: dict) -> bool:
        return any(
            [
                db_item["creation_date"] != item.get("created"),
                db_item["modification_date"] != item.get("modified"),
                db_item["publication_date"] != item.get("publication_date"),
                db_item["expiration_date"] != item.get("expiration_date"),
                db_item["type"] != item.get("type"),
                db_item["district"] != item.get("district"),
            ]
        )

    def fetch_items_data(self, items: dict) -> list:
        urls = [
            urljoin(self.iprox_detail_url, str(item_id)) for item_id in items.keys()
        ]
        logger.info(f"Starting async fetch for {len(urls)} items from IPROX")
        upsert_item_data = asyncio.run(self._async_fetch(urls))
        upsert_item_data = [
            {**item, **items[item["id"]]}
            for item in upsert_item_data
            if item and item.get("id") in items
        ]
        logger.info(
            f"Finished async fetch. Successfully collected {len(upsert_item_data)} items"
        )
        return upsert_item_data

    async def _async_fetch(self, urls):
        """Fetch all URLs with limited concurrency."""
        sem = asyncio.Semaphore(self.max_concurrent_requests)
        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_with_sem(sem, session, url) for url in urls]
            return await asyncio.gather(*tasks)

    async def _fetch_with_sem(self, sem, session, url):
        """Fetch a URL, respecting the semaphore limit."""
        async with sem:
            try:
                return await self._fetch(session, url)
            except Exception:
                logger.error(f"Failed to fetch {url}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(FetchError),
    )
    async def _fetch(self, session, url):
        """Fetch a URL, with retries on failure."""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    raise FetchError(
                        f"Failed to fetch {url}, status code: {response.status}"
                    )
                return await response.json()
        except aiohttp.ClientError as e:
            raise FetchError(f"Failed to fetch {url}: {str(e)}") from e
