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
    silent_properties_enum: type[ChoicesEnum] | None = None
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

    def _layer_url(self, *, base_url: str, layer: Dict[str, Any]) -> str:
        return f"{base_url}{layer['code']}.json"

    def _preprocess_layer_features(
        self, *, features: list[Dict[str, Any]], layer: Dict[str, Any]
    ) -> list[Dict[str, Any]]:
        return features

    def _preprocess_feature(
        self, *, feature: Dict[str, Any], layer: Dict[str, Any]
    ) -> None:
        return

    def get_full_data(self) -> Dict[str, Any]:
        base_url = self.data_url

        all_features: list[Dict[str, Any]] = []
        id_counter = 1

        for layer in self.data_layers:
            layer_label = layer["label"]
            url = self._layer_url(base_url=base_url, layer=layer)
            try:
                features = self._get_geojson_items_for_url(url)
                features = self._preprocess_layer_features(
                    features=features,
                    layer=layer,
                )
            except Exception as e:
                logger.error(f"Error fetching geojson items for URL {url}: {e}")
                features = []

            for feature in features:
                self._preprocess_feature(feature=feature, layer=layer)

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
            items=all_features,
            filters=self.filters_enum,
            layers=self.layers_enum,
            properties_to_include=self.properties_enum,
            silent_properties=self.silent_properties_enum,
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
        geom_type = geom.get("type")
        coordinates = geom.get("coordinates")

        if (
            geom_type == "Point"
            and isinstance(coordinates, list)
            and len(coordinates) == 2
        ):
            coords = coordinates

        elif geom_type == "MultiPoint":
            if (
                isinstance(coordinates, list)
                and coordinates
                and isinstance(coordinates[0], list)
            ):
                coords = coordinates[0]
            else:
                logger.error("MultiPoint geometry does not contain valid coordinates.")

        elif geom_type == "Polygon":
            if (
                isinstance(coordinates, list)
                and coordinates
                and isinstance(coordinates[0], list)
                and coordinates[0]
                and isinstance(coordinates[0][0], list)
            ):
                coords = coordinates[0][0]
            else:
                logger.error("Polygon geometry does not contain valid coordinates.")

        elif geom_type == "MultiPolygon":
            if (
                isinstance(coordinates, list)
                and coordinates
                and isinstance(coordinates[0], list)
                and coordinates[0]
                and isinstance(coordinates[0][0], list)
                and coordinates[0][0]
                and isinstance(coordinates[0][0][0], list)
            ):
                coords = coordinates[0][0][0]
            else:
                logger.error(
                    "MultiPolygon geometry does not contain valid coordinates."
                )

        else:
            logger.error(f"Unexpected geometry type: {geom_type}")

        lat = coords[1] if isinstance(coords, list) and len(coords) >= 2 else None
        lon = coords[0] if isinstance(coords, list) and len(coords) >= 2 else None

        return {
            "street": properties.get("street", ""),
            "number": properties.get("street_number", None),
            "postcode": properties.get("zip", ""),
            "city": properties.get("city", "Amsterdam"),
            "coordinates": {"lat": lat, "lon": lon},
        }
