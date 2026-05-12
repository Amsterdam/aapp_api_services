import asyncio
import logging
from urllib.parse import urljoin

import aiohttp
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


class FetchError(Exception):
    pass


class IproxFetcher:
    def __init__(
        self,
        iprox_fetch_url: str,
        iprox_detail_url: str,
        sources: list[dict],
        max_concurrent_requests: int = 20,
    ):
        """Initialize the fetcher with URLs and settings.
        Args:
            iprox_fetch_url (str): The URL to fetch the list of items.
            iprox_detail_url (str): The URL to fetch item details.
            sources (list[dict]): List of sources to fetch from.
            max_concurrent_requests (int): Maximum number of concurrent requests.
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

    def extract(self) -> list[dict]:
        """
        Main method to extract articles from the IPROX API.

        The method performs the following steps:
        1. Fetches a list of all items from the IPROX API, including their base information.
        2. Fetches the detailed information from the IPROX API.
        3. Returns a list of dictionaries containing the detailed information for all items.

        Returns:
            list[dict]: A list of dictionaries, each containing detailed information about a news article.

        In the future this method could be extended to first check which items are new or have been altered since the last fetch,
        and only then fetch the details for those items. This would reduce the number of API calls and improve performance,
        especially if the number of items is large and only a few are new or altered.
        The steps would then be:
            1. Fetches a list of all items from the IPROX API, including their base information.
            2. Queries the database for existing articles to determine which items are new or have been altered since the last fetch.
            3. For new or altered items, fetches the detailed information from the IPROX API.
            4. Returns a list of dictionaries containing the detailed information for new or altered items.
        """

        # Step 1: Extract base info for all items
        logger.info("Extracting base info for all news articles from source")
        all_iprox_items = self.fetch_all_items()

        # Step 2: Fetch details for all items
        extracted_data = self.fetch_items_details(items=all_iprox_items)
        logger.info(f"Extracted {len(extracted_data)} news articles from source")
        return extracted_data

    def fetch_all_items(self) -> dict:
        """Get a list of items from the IPROX API."""
        all_items = {}

        for source in self.sources:
            source_type = source.get("type")
            source_district = source.get("district")
            logger.info(f"Collecting list of items for source {source}")
            source_url = urljoin(
                self.iprox_fetch_url.rstrip("/") + "/", source["index"]
            )
            # We need to fetch all pages
            page = 0
            while True:
                paginated_url = f"{source_url}?page={page}"
                result = asyncio.run(self._async_fetch([paginated_url]))[0]
                if not result:
                    # no need to log an error here, because a error is already logged in the _fetch method.
                    # We just break the loop and continue with the next source.
                    break
                items = result.get("items", [])

                for item in items:
                    item["type"] = source_type
                    item["district"] = source_district
                    if item["id"] in all_items and source is not None:
                        logger.warning(
                            f"Duplicate item ID {item['id']} found. Old type: {all_items[item['id']]['type']}, new type: {source['type']}. Overwriting previous item."
                        )
                    all_items[item["id"]] = item

                pages = result.get("pages", 1)
                if page == pages - 1:
                    break
                page += 1
        return all_items

    def fetch_items_details(self, items: dict) -> list:
        urls = [
            urljoin(self.iprox_detail_url.rstrip("/") + "/", str(item_id))
            for item_id in items.keys()
        ]
        logger.info(f"Starting async fetch for {len(urls)} items from IPROX")
        item_details = asyncio.run(self._async_fetch(urls))

        item_result = []
        for item in item_details:
            if item and item.get("id") in items:
                merged_item = self._combine_detailed_and_basic_info(
                    item, items[item["id"]]
                )
                item_result.append(merged_item)

        logger.info(
            f"Finished async fetch. Successfully collected {len(item_result)} items"
        )
        return item_result

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

    def _combine_detailed_and_basic_info(
        self,
        detailed_info: dict,
        basic_info: dict,
        preserve_basic_info_keys: tuple = ("type", "district"),
    ) -> dict:
        """Combine detailed and basic information into a single dictionary."""
        combined_info = {
            **detailed_info,
            **{
                key: basic_info[key]
                for key in preserve_basic_info_keys
                if key in basic_info
            },
        }
        return combined_info
