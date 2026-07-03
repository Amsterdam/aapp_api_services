from typing import Any, Dict

from contact.enums.pride import (
    LIST_PROPERTY,
    PrideData,
    PrideFilters,
    PrideIcons,
    PrideLayers,
    PrideProperties,
    PrideSilentProperties,
)
from contact.services.event_abstract import EventAbstractService


class PrideService(EventAbstractService):
    data_enum = PrideData
    filters_enum = PrideFilters
    layers_enum = PrideLayers
    properties_enum = PrideProperties
    silent_properties_enum = PrideSilentProperties
    icons_enum = PrideIcons
    list_property = LIST_PROPERTY

    def _preprocess_feature(
        self, *, feature: Dict[str, Any], layer: Dict[str, Any]
    ) -> None:

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

        if layer_type == "Canal parade" and geom.get("type") == "LineString":
            # for canal parade we want to add stroke and stroke-width properties
            stroke = "#009DE6"
            stroke_width = 5
        else:
            stroke = None
            stroke_width = None

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

        title = properties.get("title", "")
        address = None
        if properties.get("street"):
            address = self._get_address_from_properties(properties, geom)

        return {
            f"{prefix}title": title,
            f"{prefix}subtitle": layer_type,
            f"{prefix}icon_type": icon_name,
            f"{prefix}description": self._clean_html(properties.get("description"))
            or None,
            f"{prefix}website": self._get_website(properties),
            f"{prefix}address": address,
            f"{prefix}table": self._create_table(properties.get("meta", [])),
            "fill": fill,
            "fill-opacity": fill_opacity,
            "stroke": stroke,
            "stroke-width": stroke_width,
        }
