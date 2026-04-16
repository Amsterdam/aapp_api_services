import logging
from typing import Any, Dict, List

from django.conf import settings

from contact.enums.kingsday_land import (
    LIST_PROPERTY,
    KingsdayLandData,
    KingsdayLandFilters,
    KingsdayLandIcons,
    KingsdayLandLayers,
    KingsdayLandProperties,
    KingsdayLandSilentProperties,
)
from contact.services.kingsday_abstract import KingsdayAbstractService

logger = logging.getLogger(__name__)


class KingsdayLandService(KingsdayAbstractService):
    data_enum = KingsdayLandData
    filters_enum = KingsdayLandFilters
    layers_enum = KingsdayLandLayers
    properties_enum = KingsdayLandProperties
    silent_properties_enum = KingsdayLandSilentProperties
    icons_enum = KingsdayLandIcons
    list_property = LIST_PROPERTY

    def get_full_data(self) -> Dict[str, Any]:
        base_url = self.data_url

        all_features: list[Dict[str, Any]] = []
        id_counter = 1

        for layer in self.data_layers:
            layer_label = layer["label"]

            if layer_label == "Drinkwater":  # for taps, we use a different URL
                url = settings.TAP_URL
            else:
                url = f"{base_url}{layer['code']}.json"

            try:
                features = self._get_geojson_items_for_url(url)

                if layer_label == "Drinkwater":
                    # filter taps to only include those that are within the municipality of Amsterdam,
                    # based on the "plaats" property in the properties, which should contain "Amsterdam" or "Weesp"
                    features = self._filter_tap_data(features)
            except Exception as e:
                logger.error(f"Error fetching geojson items for URL {url}: {e}")
                features = []

            for feature in features:
                feature_properties = feature.get("properties", {}) or {}

                if layer_label == "Drinkwater":
                    # for taps, we want to add the title property based on the description, as the original data does not have a title field
                    feature_properties["title"] = self._tap_title(feature_properties)
                    feature["geometry"] = self._get_tap_geometry_from_properties(
                        feature_properties
                    )

                feature_geom = feature.get("geometry", {}) or {}

                custom_properties = self.get_custom_properties(
                    feature_properties,
                    feature_geom,
                    layer_type=layer_label,
                    icon_name=layer.get("icon_label"),
                )

                feature["properties"] = {**feature_properties, **custom_properties}
                feature["id"] = id_counter
                id_counter += 1

            all_features.extend(features)

        return self.build_response_payload(
            items=all_features,
            filters=self.filters_enum,
            layers=self.layers_enum,
            properties_to_include=self.properties_enum,
            silent_properties=self.silent_properties_enum,
            list_property=self.list_property,
            icons=self.icons_enum,
        )

    def _filter_tap_data(self, data: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
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

    def _get_tap_geometry_from_properties(
        self, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Original API returns rd coordinates in the tap geometry field and lat/lon in the properties,
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

    def get_custom_properties(
        self,
        properties: Dict[str, Any],
        geom: Dict[str, Any],
        layer_type: str,
        icon_name: str | None,
    ) -> Dict[str, Any]:
        """
        Returns a dictionary of custom properties for a given data point,
        based on the original properties, geometry, layer type, and icon name.

        All custom properties are prefixed with 'aapp_' to avoid conflicts with original properties.
        However, the fill and fill_opacity properties for the 'Omleiding' layer are not prefixed,
        as they are used for styling the layer and the geojson standard is used.
        """

        prefix = self.properties_prefix

        if layer_type == "Omleiding" and geom.get("type") == "Polygon":
            # for detour we want to add fill and opacity properties
            fill = "#EC0000"
            fill_opacity = 0.2
        else:
            fill = None
            fill_opacity = None

        if layer_type == "Drinkwater":
            title = self._tap_title(properties)
            address = None  # for taps we don't want to show the address, as it is often not accurate and clutters the info box
        else:
            title = properties.get("title", "")
            address = self._get_address_from_properties(properties, geom)

        return {
            f"{prefix}title": title,
            f"{prefix}subtitle": layer_type,
            f"{prefix}icon_type": icon_name,
            f"{prefix}description": self._clean_html(properties.get("description"))
            or None,
            f"{prefix}website": properties.get("website") or None,
            f"{prefix}address": address,
            f"{prefix}toilet_table": self._create_toilet_table(
                properties.get("meta", [])
            ),
            "fill": fill,
            "fill-opacity": fill_opacity,
        }

    def _tap_title(self, properties: Dict[str, Any]) -> str:
        description = (properties.get("beschrijvi") or "").lower()
        return "Drinkfontein" if "fontein" in description else "Watertap"

    def _create_toilet_table(
        self, meta: List[Dict[str, str]]
    ) -> List[Dict[str, str]] | None:
        """
        Converts the 'meta' field from the original data into a structured format for the 'aapp_toilet_table' property.
        """
        if not meta:
            return None

        table = []
        for item in meta:
            key = item.get("title")
            value = item.get("value")
            if key and value:
                table.append({"key": key, "value": value})

        return table
