import logging
from typing import Optional, Tuple

import geopy.distance


def calculate_distance(
    coords_1: Tuple[float, float], coords_2: Tuple[float, float]
) -> Optional[int]:
    """
    Calculate the distance in meters between two coordinate pairs.

    Args:
        coords_1 (Tuple[float, float]): The first coordinate pair (latitude, longitude).
        coords_2 (Tuple[float, float]): The second coordinate pair (latitude, longitude).

    Returns:
        Optional[int]: The distance in meters, or None if the calculation fails.
    """
    try:
        if None in coords_1 or None in coords_2:
            return None
        distance_km = geopy.distance.geodesic(coords_1, coords_2).km
        return int(distance_km * 1000)
    except ValueError as e:
        logging.error(f"Invalid coordinates provided: {e}")
        return None
    except Exception as e:
        logging.exception("An unexpected error occurred while calculating distance.")
        return None
