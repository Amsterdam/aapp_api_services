import logging
import re
from typing import Optional, Tuple

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def geocode_address(address: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Convert an address to latitude and longitude using the geocoding API.

    Args:
        address (str): The address to geocode.

    Returns:
        Tuple[Optional[float], Optional[float]]: A tuple containing latitude and longitude,
        or (None, None) if the geocoding fails.
    """

    try:
        response = requests.get(
            settings.ADDRESS_SEARCH_URL,
            params=[
                ("q", address),
                ("fq", "woonplaatsnaam:(amsterdam OR weesp)"),
                ("rows", "1"),
                ("fq", "type:adres"),
            ],
            headers={"Referer": "app.amsterdam.nl"},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Error while geocoding address '{address}': {e}")
        return None, None

    data = response.json()
    results = data.get("response", {}).get("docs", [])
    if not results:
        logger.warning(f"No results found for address: {address}")
        return None, None

    coordinates = results[0].get("centroide_ll", "")
    m = re.match(r"POINT\(\s*([-0-9.]+)\s+([-0-9.]+)\s*\)", coordinates)
    lon, lat = m.groups()

    return float(lat), float(lon)
