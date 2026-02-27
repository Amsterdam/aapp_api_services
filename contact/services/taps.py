import logging
from typing import Any, Dict

from django.conf import settings

from contact.enums.taps import TapFilters, TapProperties
from contact.services.service_abstract import ServiceAbstract

logger = logging.getLogger(__name__)


class TapService(ServiceAbstract):
    data_url = settings.TAP_URL

    def __init__(self) -> None:
        super().__init__()

    def get_full_data(self) -> Dict[str, Any]:
        """
        Returns a dictionary containing:
        - filters: available filters for the frontend
        - properties_to_include: properties to include and their order
        - data: list of taps with selected and custom properties
        """
        all_taps = self.get_geojson_items()
        taps = self.filter_data(all_taps)

        full_tap_data = []
        full_types = []

        for tap in taps:
            # get properties and add custom properties with prefix to avoid conflicts with original properties,
            properties = tap.get("properties", {}) or {}
            custom_properties = self.get_custom_properties(properties)
            new_properties = {**properties, **custom_properties}

            # TODO: When out of MVP stage: implement a way to store all available properties in a database,
            # so that filters can be made on them and properties for the frontend can be selected.
            full_tap_data.append(
                {
                    "id": int(tap.get("id").split(".")[1]),
                    "geometry": self.get_geometry_from_properties(
                        tap.get("properties", {}) or {}
                    ),
                    "properties": new_properties,
                }
            )
            full_types.append(tap.get("properties", {}).get("type", ""))

        full_data = {
            "filters": TapFilters.choices(),
            "properties_to_include": TapProperties.choices(),
            "data": full_tap_data,
        }

        return full_data

    def filter_data(self, data: list[Dict[str, Any]]) -> Dict[str, Any]:
        """
        We only want to return taps that are within the municipality of Amsterdam, so we filter data based on the "plaats" property,
        which should contain "Amsterdam" or "Weesp".
        """
        filtered_data = [
            tap
            for tap in data
            if tap.get("properties", {}).get("plaats")
            in ["Amsterdam", "Weesp", "Amsterdamse bos"]
        ]
        return filtered_data

    def get_custom_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a dictionary of custom properties for a tap, using a prefix to avoid conflicts.
        """
        custom_properties = {
            f"{self.properties_prefix}is_fountain": "fontein"
            in properties.get("beschrijving", "").lower(),
            f"{self.properties_prefix}always_accessible": "24-7 open"
            in properties.get("type", "").lower(),
            f"{self.properties_prefix}has_issue": "storing"
            in properties.get("type", "").lower(),
        }
        return custom_properties

    def get_geometry_from_properties(
        self, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Original API returns rd coordinates in the geometry field and lat/lon in the properties,
        but we want to return lat/lon in the geometry field to be consistent with other services.
        """
        if (
            properties.get("latitude") is not None
            and properties.get("longitude") is not None
        ):
            return {
                "type": "Point",
                "coordinates": [
                    properties.get("longitude"),
                    properties.get("latitude"),
                ],
            }
        return {}
