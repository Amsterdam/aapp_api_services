from typing import Any, Dict

from rest_framework import serializers

from contact.enums.base import ChoicesEnum, ModuleSourceChoices, SerializerMapping
from core.serializers.address_serializers import AddressSerializer


class ServiceAddressSerializer(AddressSerializer):
    # We can be a little less strict for service addresses
    postcode = serializers.CharField(allow_null=True, allow_blank=True)
    number = serializers.CharField(allow_null=True, allow_blank=True)
    street = serializers.CharField(allow_null=True, allow_blank=True)


class KeyValueTableSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.CharField()


class PropertySerializers(ChoicesEnum):
    ADDRESS = SerializerMapping(
        type="address",
        serializer=ServiceAddressSerializer,
    )
    BOOLEAN = SerializerMapping(
        type="boolean",
        serializer=serializers.BooleanField,
    )
    IMAGE = SerializerMapping(
        type="image",
        serializer=serializers.URLField,
    )
    MALFUNCTION = SerializerMapping(
        type="malfunction",
        serializer=serializers.CharField,
    )
    PRICE = SerializerMapping(
        type="price",
        serializer=serializers.FloatField,
    )
    STRING = SerializerMapping(
        type="string",
        serializer=serializers.CharField,
    )
    TABLE = SerializerMapping(
        type="key_value_table",
        serializer=KeyValueTableSerializer,
    )
    URL = SerializerMapping(
        type="url",
        serializer=serializers.URLField,
    )


class FilterSerializers(ChoicesEnum):
    BOOL = SerializerMapping(
        type="bool",
        serializer=serializers.BooleanField,
    )
    INT = SerializerMapping(
        type="int",
        serializer=serializers.IntegerField,
    )
    STR = SerializerMapping(
        type="str",
        serializer=serializers.CharField,
    )


property_serializer_mapping = {
    item.value.type: item.value.serializer for item in PropertySerializers
}
filter_serializer_mapping = {
    item.value.type: item.value.serializer for item in FilterSerializers
}


def build_dynamic_properties_serializer(
    properties: list[Dict[str, Any]],
    filters: list[Dict[str, Any]],
    layers: list[Dict[str, Any]],
    list_property: Dict[str, Any] | None,
    include_icons: bool = True,
) -> serializers.Serializer:
    """
    Dynamically constructs a serializer class based on given properties and filters.
    """

    fields = {
        "aapp_title": serializers.CharField(),
        "aapp_subtitle": serializers.CharField(
            allow_null=True, allow_blank=True, required=False
        ),
    }  # Always include title and subtitle as a property

    if include_icons:
        fields["aapp_icon_type"] = serializers.CharField()

    # Add property fields
    for prop in properties:
        field_class = property_serializer_mapping.get(
            prop.get("property_type"), serializers.CharField
        )
        if prop.get("property_type") == "key_value_table":
            fields[prop["property_key"]] = field_class(many=True, allow_null=True)
        else:
            fields[prop["property_key"]] = field_class(allow_null=True)

    # Add filter fields (if not already included)
    for filt in filters:
        key = filt["filter_key"]
        if key not in fields:
            field_class = filter_serializer_mapping.get(
                type(filt["filter_value"]).__name__, serializers.CharField
            )
            fields[key] = field_class()

    # Add layer fields (if not already included)
    for layer in layers:
        key = layer["filter_key"]
        if key not in fields:
            field_class = filter_serializer_mapping.get(
                type(layer["filter_value"]).__name__, serializers.CharField
            )
            fields[key] = field_class()

    if list_property:
        key = list_property["key"]
        if key not in fields:
            field_class = property_serializer_mapping.get(
                list_property["type"], serializers.CharField
            )
            # TODO: change required to True once addresses are added for taps
            fields[key] = field_class(allow_null=True, required=False)

    return type("DynamicPropertiesSerializer", (serializers.Serializer,), fields)


def build_service_list_serializer(
    properties: list[Dict[str, Any]],
    filters: list[Dict[str, Any]],
    layers: list[Dict[str, Any]],
    list_property: Dict[str, Any],
    include_icons: bool = True,
) -> serializers.Serializer:
    DynamicPropertiesSerializer = build_dynamic_properties_serializer(
        properties, filters, layers, list_property, include_icons
    )

    class DynamicServiceListSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        type = serializers.CharField()
        geometry = GeometrySerializer()
        properties = DynamicPropertiesSerializer()

    return DynamicServiceListSerializer


def build_geojson_serializer(
    properties: list[Dict[str, Any]],
    filters: list[Dict[str, Any]],
    layers: list[Dict[str, Any]],
    list_property: Dict[str, Any],
    include_icons: bool = True,
) -> serializers.Serializer:
    DynamicListSerializer = build_service_list_serializer(
        properties, filters, layers, list_property, include_icons
    )

    class DynamicGeoJsonSerializer(serializers.Serializer):
        type = serializers.CharField()
        features = DynamicListSerializer(many=True)

    return DynamicGeoJsonSerializer


def build_map_response_serializer(
    properties: list[Dict[str, Any]],
    filters: list[Dict[str, Any]],
    layers: list[Dict[str, Any]],
    list_property: Dict[str, Any],
    include_icons: bool = True,
) -> serializers.Serializer:
    DynamicGeoJsonSerializer = build_geojson_serializer(
        properties, filters, layers, list_property, include_icons
    )

    class DynamicMapResponseSerializer(ServiceMapResponseSerializer):
        data = DynamicGeoJsonSerializer()

    return DynamicMapResponseSerializer


class ServiceMapsRequestSerializer(serializers.Serializer):
    module_source = serializers.ChoiceField(
        choices=[choice.value for choice in ModuleSourceChoices],
        default=ModuleSourceChoices.HANDIG_IN_DE_STAD.value,
        help_text="Filter services based on their input module. Default is 'handig-in-de-stad'.",
    )


class ServiceMapsResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    icon = serializers.CharField()


class FlexibleValueField(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        if isinstance(data, (int, str, bool)):
            return data
        raise serializers.ValidationError("filter_value must be int, str, or bool")


class FiltersSerializer(serializers.Serializer):
    label = serializers.CharField()
    filter_key = serializers.CharField()
    filter_value = FlexibleValueField()


class PropertiesSerializer(serializers.Serializer):
    label = serializers.CharField(allow_null=True)
    property_key = serializers.CharField()
    property_type = serializers.CharField()
    icon = serializers.CharField(allow_null=True)


class ListPropertySerializer(serializers.Serializer):
    key = serializers.CharField()
    type = serializers.CharField()


class GeometrySerializer(serializers.Serializer):
    type = serializers.CharField()
    coordinates = serializers.JSONField()

    @staticmethod
    def _is_number(value: Any) -> bool:
        return isinstance(value, float)

    def validate(self, attrs):
        geometry_type = attrs.get("type")
        coordinates = attrs.get("coordinates")

        if geometry_type == "Point":
            if not (
                isinstance(coordinates, list)
                and len(coordinates) >= 2
                and self._is_number(coordinates[0])
                and self._is_number(coordinates[1])
            ):
                raise serializers.ValidationError(
                    {"coordinates": "Point coordinates must be [lon, lat]."}
                )

        if geometry_type == "Polygon":
            # Expect: [ [ [lon, lat], ... ] , ... ] (one or more rings)
            if not (
                isinstance(coordinates, list)
                and coordinates
                and isinstance(coordinates[0], list)
                and coordinates[0]
                and isinstance(coordinates[0][0], list)
                and len(coordinates[0][0]) >= 2
                and self._is_number(coordinates[0][0][0])
                and self._is_number(coordinates[0][0][1])
            ):
                raise serializers.ValidationError(
                    {
                        "coordinates": "Polygon coordinates must be nested [lon, lat] positions."
                    }
                )

        if geometry_type == "LineString":
            # Expect: [ [lon, lat], ... ] (one or more positions)
            if not (
                isinstance(coordinates, list)
                and coordinates
                and isinstance(coordinates[0], list)
                and len(coordinates[0]) >= 2
                and self._is_number(coordinates[0][0])
                and self._is_number(coordinates[0][1])
            ):
                raise serializers.ValidationError(
                    {
                        "coordinates": "LineString coordinates must be [lon, lat] positions."
                    }
                )

        return attrs


class ServiceListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    geometry = GeometrySerializer()
    properties = serializers.DictField()


class IconDefinitionSerializer(serializers.Serializer):
    path = serializers.CharField()
    path_color = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    circle_color = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )


class ServiceMapGeoJsonSerializer(serializers.Serializer):
    type = serializers.CharField()
    features = ServiceListSerializer(many=True)


class ServiceMapResponseSerializer(serializers.Serializer):
    filters = FiltersSerializer(many=True)
    layers = FiltersSerializer(many=True)
    properties_to_include = PropertiesSerializer(many=True)
    list_property = ListPropertySerializer(allow_null=True)
    icons_to_include = serializers.DictField(
        child=IconDefinitionSerializer(), allow_null=True
    )
    data = ServiceMapGeoJsonSerializer()
