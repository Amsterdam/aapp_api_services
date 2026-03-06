import logging
from typing import Any, Dict

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from contact.enums.base import ChoicesEnum, ListPropertyClass

logger = logging.getLogger(__name__)


class ServiceAbstract:
    data_url: str = None
    properties_prefix: str = "aapp_"

    def __init__(self) -> None:
        if not self.data_url:
            raise NotImplementedError("Subclasses must define a data_url")

    def get_full_data(self) -> Dict[str, Any]:
        """
        Returns a dictionary containing:
        - filters: available filters for the frontend
        - properties_to_include: properties to include and their order
        - list_property: property that is shown in the list view
        - data: list of items with selected and custom properties
        """
        raise NotImplementedError("Subclasses must implement the get_full_data method")

    def get_geojson_items(self) -> list[Dict[str, Any]]:
        """Fetches and returns the list of items from the remote API."""
        response = self._make_request()
        return response.json().get("features", []) if response is not None else []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,  # Reraise the RequestException after retries
    )
    def _make_request(self) -> requests.Response:
        """Make the HTTP request for toilet data with retries and a timeout."""
        try:
            response = requests.get(self.data_url, timeout=5)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            logger.info("Failed to fetch data", extra={"url": self.data_url})
            raise

    def build_response_payload(
        self,
        items: list[Dict[str, Any]],
        filters: ChoicesEnum,
        properties_to_include: ChoicesEnum,
        list_property: ListPropertyClass,
    ) -> Dict[str, Any]:
        """
        Builds the response payload with the given items, filters, and properties to include.
        """
        full_data = {
            "filters": filters.choices(),
            "properties_to_include": properties_to_include.choices(),
            "list_property": list_property._asdict(),
            "data": {
                "type": "FeatureCollection",
                "features": items,
            },
        }
        return full_data
