import logging
import re
import time

from django.db import OperationalError

logger = logging.getLogger(__name__)


class DatabaseRetryMiddleware:
    """
    New-style middleware for Django 1.10+ that retries a request when a database
    connection timeout occurs.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.max_retries = 3
        self.initial_delay = 1  # seconds
        self.error_pattern = re.compile(
            r"(Operation timed out|Connection refused)", re.IGNORECASE
        )

    def __call__(self, request):
        retry_count = 0
        delay = self.initial_delay

        while True:
            try:
                response = self.get_response(request)
                return response
            except OperationalError as e:
                exception_message = str(e)
                if self.error_pattern.search(exception_message):
                    if retry_count < self.max_retries:
                        retry_count += 1
                        logger.warning(
                            f"OperationalError encountered. Retrying request {retry_count}/{self.max_retries} after {delay} seconds."
                        )
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                        continue
                # If it's not a timeout error or retries are exhausted, re-raise the exception
                raise
