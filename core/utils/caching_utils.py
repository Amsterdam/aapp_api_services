import functools
import hashlib

from django.core.cache import cache


def cache_function(timeout: int):
    """
    Decorator to cache function results for timeout seconds. Cache key is based on function name and arguments.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # If method: remove 'self' from args, or use instance identifier
            if args and hasattr(args[0], "__class__"):
                args = args[1:]  # Remove 'self' from args
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


def cache_instance_independent_function(timeout: int):
    """
    Decorator to cache function results for timeout seconds. Cache key is based on function name and arguments.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Stable cache key based on function + arguments (removed self from args in cache key)
            raw_key = f"{func.__module__}.{func.__qualname__}:{args[1:]}:{kwargs}"
            cache_key = f"aapp:{hashlib.sha256(raw_key.encode()).hexdigest()}"

            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data

            result = func(*args, **kwargs)

            cache.set(cache_key, result, timeout=timeout)
            return result

        return wrapper

    return decorator
