import asyncio
import logging
from typing import List

import aiohttp
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


class FetchError(Exception):
    pass


async def _async_fetch(
    urls: List[str], max_concurrent_requests: int = 20, timeout_total: float = 30.0
):
    """Fetch all URLs with limited concurrency and timeouts."""
    sem = asyncio.Semaphore(max_concurrent_requests)
    timeout = aiohttp.ClientTimeout(total=timeout_total)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [_fetch_with_sem(sem, session, url) for url in urls]
        return await asyncio.gather(*tasks)


async def _fetch_with_sem(
    sem: asyncio.Semaphore, session: aiohttp.ClientSession, url: str
):
    """Fetch a URL, respecting the semaphore limit."""
    async with sem:
        try:
            return await _fetch(session, url)
        except Exception as e:
            logger.error(f"Failed to fetch {url}", exc_info=e)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(FetchError),
)
async def _fetch(session: aiohttp.ClientSession, url: str):
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
