import logging
from typing import Any, Dict

from django.conf import settings

from contact.enums.taps import LIST_PROPERTY, TapFilters, TapProperties
from contact.services.address import AddressService
from contact.services.service_abstract import ServiceAbstract

logger = logging.getLogger(__name__)


class TapService(ServiceAbstract):
    data_url = settings.TAP_URL
    address_service = AddressService()

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

        coords, tap_coords = self.get_all_coordinates(taps)
        address_map = self.address_service.batch_get_addresses_by_coordinates(coords)

        full_tap_data = []
        for tap, lat, lon in tap_coords:
            properties = tap.get("properties", {}) or {}
            address = address_map.get((lat, lon))
            custom_properties = self.get_custom_properties(properties, address)
            new_properties = {**properties, **custom_properties}

            # TODO: When out of MVP stage: implement a way to store all available properties in a database,
            # so that filters can be made on them and properties for the frontend can be selected.
            full_tap_data.append(
                {
                    "id": int(tap.get("id").split(".")[1]),
                    "type": tap.get("type"),
                    "geometry": self.get_geometry_from_properties(
                        tap.get("properties", {}) or {}
                    ),
                    "properties": new_properties,
                }
            )

        full_data = self.build_response_payload(
            full_tap_data, TapFilters, TapProperties, LIST_PROPERTY
        )

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

    def get_all_coordinates(
        self, data: list[Dict[str, Any]]
    ) -> tuple[set[tuple[float, float]], list[tuple[Dict[str, Any], float, float]]]:
        """
        Extracts all unique coordinates from the tap data.
        """
        # Collect all unique coordinates
        coords = set()
        tap_coords = []
        for tap in data:
            properties = tap.get("properties", {}) or {}
            lat = properties.get("latitude")
            lon = properties.get("longitude")
            tap_coords.append((tap, lat, lon))
            if lat is not None and lon is not None:
                coords.add((lat, lon))
        return list(coords), tap_coords

    def get_custom_properties(
        self, properties: Dict[str, Any], address: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Returns a dictionary of custom properties for a tap, using a prefix to avoid conflicts.
        """
        custom_properties = {
            f"{self.properties_prefix}title": properties.get("beschrijvi", "")
            or "Kraan",
            f"{self.properties_prefix}is_fountain": "fontein"
            in properties.get("beschrijvi", "").lower(),
            f"{self.properties_prefix}always_accessible": "24-7 open"
            in properties.get("type", "").lower(),
            f"{self.properties_prefix}has_issue": "storing"
            in properties.get("type", "").lower(),
            f"{self.properties_prefix}address": address if address else None,
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
