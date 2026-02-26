import logging
from typing import Any, Dict
from urllib.parse import quote

import requests
from django.conf import settings
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from contact.enums.toilets import ToiletFilters, ToiletProperties

logger = logging.getLogger(__name__)

PROPERTIES_PREFIX = "aapp_"


class ToiletService:
    def __init__(self) -> None:
        self.data_url = settings.PUBLIC_TOILET_URL
        self.image_url = settings.PUBLIC_TOILET_IMAGE_BASE_URL

    def get_full_data(self) -> Dict[str, Any]:
        """
        Returns a dictionary containing:
        - filters: available filters for the frontend
        - properties_to_include: properties to include and their order
        - data: list of toilets with selected and custom properties
        """
        toilets = self.get_toilets()

        full_toilet_data = []

        for toilet in toilets:
            # get properties and add custom properties with prefix to avoid conflicts with original properties,
            properties = toilet.get("properties", {}) or {}
            custom_properties = self.get_custom_properties(
                properties, prefix=PROPERTIES_PREFIX
            )
            new_properties = {**properties, **custom_properties}

            # TODO: When out of MVP stage: implement a way to store all available properties in a database,
            # so that filters can be made on them and properties for the frontend can be selected.
            full_toilet_data.append(
                {
                    "id": toilet.get("id"),
                    "geometry": toilet.get("geometry"),
                    "properties": new_properties,
                }
            )

        full_data = {
            "filters": ToiletFilters.choices(),
            "properties_to_include": ToiletProperties.choices(),
            "data": full_toilet_data,
        }

        return full_data

    def get_toilets(self):
        """Fetches and returns the list of toilets from the remote API."""
        response = self._make_request()
        return response.json().get("features", []) if response is not None else []

    def get_custom_properties(
        self, properties: Dict[str, Any], prefix: str
    ) -> Dict[str, Any]:
        """
        Returns a dictionary of custom properties for a toilet, using a prefix to avoid conflicts.
        """
        open_days = properties.get("Dagen_geopend", "")
        opening_times = properties.get("Openingstijden", "")
        open_hours = f"{open_days} {opening_times}".strip() or None

        picture = properties.get("Foto")
        image_url = f"{self.image_url}{quote(picture)}" if picture else None

        selectie = (properties.get("SELECTIE") or "").lower()
        return {
            f"{prefix}open_hours": open_hours,
            f"{prefix}description": properties.get("Omschrijving") or None,
            f"{prefix}image_url": image_url,
            f"{prefix}is_accessible": selectie == "toegang",
            f"{prefix}is_toilet": selectie in ("toegang", "openbaar", "parkeer"),
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,  # Reraise the RequestException after retries
    )
    def _make_request(self) -> requests.Response:
        """Make the HTTP request for toilet data with retries and a timeout."""
        try:
            response = requests.get(self.data_url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            logger.info("Failed to fetch public toilet data")
            raise
