"""Fetch all news article data from IPROX via its API (object-oriented, sync/async capable)"""

import asyncio
import logging
from datetime import datetime
from urllib.parse import urljoin

import aiohttp
from django.conf import settings
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed


class FetchError(Exception):
    pass


class IproxFetcher:
    def __init__(
        self,
        iprox_fetch_url: str,
        iprox_detail_url: str,
        sources: list[dict] | None = None,
        max_concurrent_requests: int = 20,
    ):
        self.iprox_fetch_url = iprox_fetch_url
        self.iprox_detail_url = iprox_detail_url
        self.sources = sources
        self.max_concurrent_requests = max_concurrent_requests
        self.logger = logging.getLogger(__name__)

    def fetch_all_items(self) -> dict:
        """Get a list of items from the IPROX API."""
        all_items = {}
        if self.sources is None:
            source_url = urljoin(self.iprox_fetch_url)
            result = asyncio.run(self._async_fetch([source_url]))[0]
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
            self.logger.info(f"Collecting list of items for source {source}")
            source_url = urljoin(self.iprox_fetch_url, source["index"])
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
                    self.logger.warning(
                        f"Duplicate item ID {item['id']} found. Old type: {all_items[item['id']]['type']}, new type: {source['type']}. Overwriting previous item."
                    )
                all_items[item["id"]] = item
        return all_items

    def fetch_items_data(self, items: dict) -> list:
        urls = [
            urljoin(self.iprox_detail_url, str(item_id)) for item_id in items.keys()
        ]
        self.logger.info(f"Starting async fetch for {len(urls)} items from IPROX")
        upsert_item_data = asyncio.run(self._async_fetch(urls))
        upsert_item_data = [
            {**item, **items[item["id"]]}
            for item in upsert_item_data
            if item and item.get("id") in items
        ]
        self.logger.info(
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
                self.logger.error(f"Failed to fetch {url}")

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
