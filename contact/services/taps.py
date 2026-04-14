import logging
from typing import Any, Dict, Tuple

from django.conf import settings

from contact.enums.taps import TapFilters, TapIcons, TapLayers, TapProperties
from contact.services.service_abstract import ServiceAbstract

logger = logging.getLogger(__name__)


class TapService(ServiceAbstract):
    data_url = settings.TAP_URL

    def __init__(self) -> None:
        super().__init__()

    def get_full_data(self) -> Dict[str, Any]:
        all_taps = self.get_geojson_items()
        taps = self.filter_data(all_taps)

        full_tap_data = []

        for tap in taps:
            properties = tap.get("properties", {}) or {}
            custom_properties = self.get_custom_properties(properties)
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
            full_tap_data,
            TapFilters,
            TapLayers,
            TapProperties,
            list_property=None,
            icons=TapIcons,
        )

        return full_data

    def filter_data(self, data: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
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
        title = self._tap_title(properties)
        property_type = properties.get("type", "") or ""

        custom_type, malfunction_property, has_malfunction = (
            self._tap_custom_type_and_malfunction(property_type)
        )
        icon_type = self._tap_icon_type(title=title, has_malfunction=has_malfunction)

        return self._build_custom_properties(
            title=title,
            malfunction_property=malfunction_property,
            custom_type=custom_type,
            icon_type=icon_type,
        )

    def _tap_title(self, properties: Dict[str, Any]) -> str:
        description = (properties.get("beschrijvi") or "").lower()
        return "Drinkfontein" if "fontein" in description else "Watertap"

    def _tap_custom_type_and_malfunction(
        self, property_type: str
    ) -> Tuple[str | None, str | None, bool]:
        if "storing" in property_type.lower():
            return None, "Tijdelijk buiten gebruik", True

        if "24-7" in property_type:
            return "24 uur per dag beschikbaar", None, False

        return property_type, None, False

    def _tap_icon_type(self, *, title: str, has_malfunction: bool) -> str:
        if has_malfunction:
            return TapIcons.MALFUNCTION.value.label

        if title == "Drinkfontein":
            return TapIcons.FOUNTAIN.value.label

        return TapIcons.TAP.value.label

    def _build_custom_properties(
        self,
        *,
        title: str,
        malfunction_property: str | None,
        custom_type: str | None,
        icon_type: str,
    ) -> Dict[str, Any]:
        prefix = self.properties_prefix
        return {
            f"{prefix}title": title,
            f"{prefix}malfunction": malfunction_property,
            f"{prefix}type": custom_type,
            f"{prefix}icon_type": icon_type,
        }

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
