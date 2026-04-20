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
from contact.services.taps import (
    tap_geometry_from_properties,
    tap_is_in_amsterdam_municipality,
    tap_title_from_properties,
)


class KingsdayLandService(KingsdayAbstractService):
    data_enum = KingsdayLandData
    filters_enum = KingsdayLandFilters
    layers_enum = KingsdayLandLayers
    properties_enum = KingsdayLandProperties
    silent_properties_enum = KingsdayLandSilentProperties
    icons_enum = KingsdayLandIcons
    list_property = LIST_PROPERTY

    def _layer_url(self, *, base_url: str, layer: Dict[str, Any]) -> str:
        if layer.get("label") == "Drinkwater":
            return settings.TAP_URL
        return super()._layer_url(base_url=base_url, layer=layer)

    def _preprocess_layer_features(
        self, *, features: list[Dict[str, Any]], layer: Dict[str, Any]
    ) -> list[Dict[str, Any]]:
        if layer.get("label") != "Drinkwater":
            return features

        return [
            tap
            for tap in features
            if tap_is_in_amsterdam_municipality(tap.get("properties", {}) or {})
        ]

    def _preprocess_feature(
        self, *, feature: Dict[str, Any], layer: Dict[str, Any]
    ) -> None:

        if layer.get("label") != "Drinkwater":
            # if geometry is a multipoint, convert it to a point with the coordinates of the first point, as the frontend expects a point geometry for taps
            geom = feature.get("geometry", {}) or {}
            if (
                geom.get("type") == "MultiPoint"
                and isinstance(geom.get("coordinates"), list)
                and len(geom["coordinates"]) > 0
            ):
                feature["geometry"] = {
                    "type": "Point",
                    "coordinates": geom["coordinates"][0],
                }
            return

        properties = feature.get("properties", {}) or {}
        properties["title"] = tap_title_from_properties(properties)
        feature["properties"] = properties
        feature["geometry"] = tap_geometry_from_properties(properties)

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

        if layer_type == "Omleiding" and geom.get("type") in [
            "Polygon",
            "MultiPolygon",
        ]:
            # for detour we want to add fill and opacity properties
            fill = "#EC0000"
            fill_opacity = 0.2
            stroke = "#EC0000"
            stroke_width = 2
        else:
            fill = None
            fill_opacity = None
            stroke = None
            stroke_width = None

        if layer_type == "Drinkwater":
            title = tap_title_from_properties(properties)
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
            "stroke": stroke,
            "stroke-width": stroke_width,
        }

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
