import functools
import hashlib
from datetime import datetime, timedelta

from django.core.cache import cache
from django.utils import timezone

from core.exceptions import ApiKeyInvalidException
from core.utils.coordinates_utils import wgs_to_rd
from core.utils.openapi_utils import custom_extend_schema


def seconds_until_next_expiry_hour(expiry_hours: list[int]) -> int:
    """
    Returns seconds until the next expiry time:
    04:00, 10:00, 16:00, or 22:00 (local timezone).
    """
    now = timezone.now()
    today = now.date()
    candidates_today = [
        datetime(
            year=today.year,
            month=today.month,
            day=today.day,
            hour=hour,
            minute=0,
            second=0,
            tzinfo=now.tzinfo,
        )
        for hour in expiry_hours
    ]

    # Pick the first future boundary
    for boundary in candidates_today:
        if boundary > now:
            return int((boundary - now).total_seconds())

    # Otherwise, next days first boundary
    tomorrow = today + timedelta(days=1)
    tomorrow_morning = datetime(
        year=tomorrow.year,
        month=tomorrow.month,
        day=tomorrow.day,
        hour=expiry_hours[0],
        minute=0,
        second=0,
        tzinfo=now.tzinfo,
    )
    return int((tomorrow_morning - now).total_seconds())


def cache_until_expiry_hour(expiry_hours: list[int]):
    """
    Decorator to cache function results until the next specified time boundaries.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Stable cache key based on function + arguments
            raw_key = f"{func.__module__}.{func.__qualname__}:{args}:{kwargs}"
            cache_key = hashlib.md5(raw_key.encode()).hexdigest()

            cached = cache.get(cache_key)
            if cached is not None:
                return cached

            result = func(*args, **kwargs)

            timeout = seconds_until_next_expiry_hour(expiry_hours)
            if timeout > 60:  # Only cache if timeout is more than 1 minute
                cache.set(cache_key, result, timeout=timeout)
            return result

        return wrapper

    return decorator


def calculate_rd_bbox_from_wsg_coordinates(lon: float, lat: float) -> dict[str, float]:
    """
    Given WGS84 coordinates (longitude, latitude), calculate a bounding box in Rijksdriehoek coordinates.
    The bounding box is defined as a square of 200m x 200m centered around the given point.

    Args:
        lon (float): Longitude in decimal degrees.
        lat (float): Latitude in decimal degrees.

    Returns:
        tuple: A tuple representing the bounding box in Rijksdriehoek coordinates
               (min_x, min_y, max_x, max_y).
    """
    center_x, center_y = wgs_to_rd(lon, lat)
    half_size = 100  # 100 meters in each direction to make a 200m x 200m box

    return {
        "min_x": center_x - half_size,
        "min_y": center_y - half_size,
        "max_x": center_x + half_size,
        "max_y": center_y + half_size,
    }


def extend_schema_for_burning_guide(
    success_response=None, exceptions=None, serializer_as_params=None, **kwargs
):
    additional_params = []
    if serializer_as_params:
        additional_params.append(serializer_as_params)

    return custom_extend_schema(
        default_exceptions=[ApiKeyInvalidException],
        success_response=success_response,
        exceptions=exceptions,
        additional_params=additional_params,
        **kwargs,
    )
