import asyncio
import logging
import re
import time
from asyncio import iscoroutinefunction

from django.db import OperationalError
from django.utils.decorators import sync_and_async_middleware
from psycopg2 import OperationalError as PsycopgOperationalError

logger = logging.getLogger(__name__)


@sync_and_async_middleware
def database_retry_middleware(get_response):
    max_retries = 3
    initial_delay = 1
    error_pattern = re.compile(
        r"(Operation timed out|Connection refused)", re.IGNORECASE
    )

    async def _async(request):
        retry_count = 0
        delay = initial_delay

        while True:
            try:
                return await get_response(request)
            except asyncio.CancelledError:
                # Client disconnected / request cancelled; do NOT swallow this.
                raise
            except (OperationalError, PsycopgOperationalError) as e:
                msg = str(e)
                if error_pattern.search(msg) and retry_count < max_retries:
                    retry_count += 1
                    logger.warning(
                        f"OperationalError encountered. Retrying request {retry_count}/{max_retries} after {delay} seconds."
                    )
                    await asyncio.sleep(delay)  # <-- key fix for async
                    delay *= 2
                    continue
                raise

    def _sync(request):
        retry_count = 0
        delay = initial_delay

        while True:
            try:
                return get_response(request)
            except (OperationalError, PsycopgOperationalError) as e:
                msg = str(e)
                if error_pattern.search(msg) and retry_count < max_retries:
                    retry_count += 1
                    logger.warning(
                        f"OperationalError encountered. Retrying request {retry_count}/{max_retries} after {delay} seconds."
                    )
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise

    return _async if iscoroutinefunction(get_response) else _sync
