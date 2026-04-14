import logging
import re
from typing import Any, Dict

from django.conf import settings

from contact.enums.base import ChoicesEnum, ListPropertyClass
from contact.services.service_abstract import ServiceAbstract

logger = logging.getLogger(__name__)


class KingsdayAbstractService(ServiceAbstract):
    """Shared Kingsday geojson-to-map-service implementation.

    Concrete subclasses only need to provide the Kingsday-specific enums:
    - data_enum: provides the data layers to fetch
    - filters_enum, layers_enum, properties_enum, icons_enum, list_property

    The base class keeps `data_url` stable across calls (it temporarily swaps it
    per request) so repeated `get_full_data()` calls remain correct.
    """

    data_url = settings.KINGSDAY_URL

    data_enum: type[ChoicesEnum] | None = None
    filters_enum: type[ChoicesEnum] | None = None
    layers_enum: type[ChoicesEnum] | None = None
    properties_enum: type[ChoicesEnum] | None = None
    icons_enum: type[ChoicesEnum] | None = None
    list_property: ListPropertyClass | None = None

    _clean_html_re = re.compile(r"<.*?>")

    def __init__(self) -> None:
        super().__init__()
        if self.data_enum is None:
            raise NotImplementedError("Subclasses must define data_enum")
        if self.filters_enum is None:
            raise NotImplementedError("Subclasses must define filters_enum")
        if self.layers_enum is None:
            raise NotImplementedError("Subclasses must define layers_enum")
        if self.properties_enum is None:
            raise NotImplementedError("Subclasses must define properties_enum")

        self.data_layers = self.data_enum.choices_as_list()

    def get_full_data(self) -> Dict[str, Any]:
        base_url = self.data_url

        all_features: list[Dict[str, Any]] = []
        id_counter = 1

        for layer in self.data_layers:
            layer_label = layer["label"]
            url = f"{base_url}{layer['code']}.json"
            features = self._get_geojson_items_for_url(url)

            for feature in features:
                feature_properties = feature.get("properties", {}) or {}
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
            all_features,
            self.filters_enum,
            self.layers_enum,
            self.properties_enum,
            list_property=self.list_property,
            icons=self.icons_enum,
        )

    def _get_geojson_items_for_url(self, url: str) -> list[Dict[str, Any]]:
        """Fetch geojson features for a specific URL without leaving state behind."""
        previous_url = self.data_url
        try:
            self.data_url = url
            return self.get_geojson_items()
        finally:
            self.data_url = previous_url

    def get_custom_properties(
        self,
        properties: Dict[str, Any],
        geom: Dict[str, Any],
        layer_type: str,
        icon_name: str | None,
    ) -> Dict[str, Any]:
        address = self._get_address_from_properties(properties, geom)
        prefix = self.properties_prefix

        return {
            f"{prefix}title": properties.get("title", ""),
            f"{prefix}subtitle": layer_type,
            f"{prefix}icon_type": icon_name,
            f"{prefix}description": self._clean_html(properties.get("description"))
            or None,
            f"{prefix}website": properties.get("website") or None,
            f"{prefix}address": address,
        }

    def _clean_html(self, raw_html: Any) -> str:
        if not raw_html:
            return ""
        return re.sub(self._clean_html_re, "", str(raw_html))

    def _get_address_from_properties(
        self, properties: Dict[str, Any], geom: Dict[str, Any]
    ) -> Dict[str, Any]:

        coords = None

        if (
            geom.get("type") == "Point"
            and isinstance(geom.get("coordinates"), list)
            and len(geom.get("coordinates")) == 2
        ):
            coords = geom["coordinates"]

        elif geom.get("type") == "MultiPoint":
            if (
                isinstance(geom.get("coordinates"), list)
                and len(geom["coordinates"]) > 0
            ):
                geom["coordinates"] = geom["coordinates"][0]
                geom["type"] = "Point"
                coords = geom["coordinates"]
            else:
                logger.error("MultiPoint geometry does not contain valid coordinates.")

        elif geom.get("type") == "Polygon":
            if (
                isinstance(geom.get("coordinates"), list)
                and len(geom.get("coordinates")) > 0
                and isinstance(geom["coordinates"][0], list)
                and len(geom["coordinates"][0]) > 0
            ):
                coords = geom["coordinates"][0][0]
            else:
                logger.error("Polygon geometry does not contain valid coordinates.")

        else:
            logger.error(f"Unexpected geometry type: {geom.get('type')}")

        lat = coords[1] if isinstance(coords, list) and len(coords) >= 2 else None
        lon = coords[0] if isinstance(coords, list) and len(coords) >= 2 else None

        address_object = {
            "street": properties.get("street", ""),
            "number": properties.get("street_number", None),
            "postcode": properties.get("zip", ""),
            "city": properties.get("city", "Amsterdam"),
            "coordinates": {"lat": lat, "lon": lon},
        }

        return address_object
