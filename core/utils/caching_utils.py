import functools
import hashlib
import inspect
import os
import sys

from django.core.cache import cache


def cache_function(timeout: int):
    """
    Decorator to cache function results for timeout seconds. Cache key is based on function name and arguments.
    """

    def decorator(func):
        def should_bypass_cache() -> bool:
            # Pytest runs against a persistent Redis cache in this repo's docker setup.
            # That means cache entries can leak between tests and make DB-driven code
            # behave non-deterministically. To keep tests reliable, bypass caching.
            pytest_running = "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST")
            cache_flag = (
                os.getenv("CACHE_FUNCTION_ENABLED_PYTEST", default="").lower() == "true"
            )
            bypass_flag = pytest_running and not cache_flag
            return bypass_flag

        def get_cache_key(args, kwargs) -> str:
            # Stable cache key based on function + arguments
            raw_key = f"{func.__module__}.{func.__qualname__}:{args}:{kwargs}"
            return f"aapp:{hashlib.sha256(raw_key.encode()).hexdigest()}"

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                if should_bypass_cache():
                    return await func(*args, **kwargs)

                cache_key = get_cache_key(args, kwargs)
                cached_data = cache.get(cache_key)
                if cached_data is not None:
                    return cached_data

                result = await func(*args, **kwargs)
                cache.set(cache_key, result, timeout=timeout)
                return result

        else:

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if should_bypass_cache():
                    return func(*args, **kwargs)

                cache_key = get_cache_key(args, kwargs)
                cached_data = cache.get(cache_key)
                if cached_data is not None:
                    return cached_data

                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout=timeout)
                return result

        return wrapper

    return decorator
