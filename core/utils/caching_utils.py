import functools
import hashlib
import os
import sys

from django.core.cache import cache


def cache_function(timeout: int):
    """
    Decorator to cache function results for timeout seconds. Cache key is based on function name and arguments.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Pytest runs against a persistent Redis cache in this repo's docker setup.
            # That means cache entries can leak between tests and make DB-driven code
            # behave non-deterministically. To keep tests reliable, bypass caching.
            pytest_running = "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST")
            cache_flag = os.getenv("CACHE_FUNCTION_ENABLED_PYTEST")
            caching_enabled_in_pytest = (
                cache_flag is not None and cache_flag.lower() == "true"
            )
            if pytest_running and not caching_enabled_in_pytest:
                return func(*args, **kwargs)

            # Stable cache key based on function + arguments
            raw_key = f"{func.__module__}.{func.__qualname__}:{args}:{kwargs}"
            cache_key = f"aapp:{hashlib.sha256(raw_key.encode()).hexdigest()}"

            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data

            result = func(*args, **kwargs)

            cache.set(cache_key, result, timeout=timeout)
            return result

        return wrapper

    return decorator
