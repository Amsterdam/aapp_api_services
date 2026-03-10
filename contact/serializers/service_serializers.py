from typing import Any, Dict

from rest_framework import serializers

from contact.enums.base import ChoicesEnum, SerializerMapping


class PropertySerializers(ChoicesEnum):
    BOOLEAN = SerializerMapping(
        type="boolean",
        serializer=serializers.BooleanField,
    )
    IMAGE = SerializerMapping(
        type="image",
        serializer=serializers.URLField,
    )
    PRICE = SerializerMapping(
        type="price",
        serializer=serializers.FloatField,
    )
    STRING = SerializerMapping(
        type="string",
        serializer=serializers.CharField,
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
    list_property: Dict[str, Any] | None,
) -> serializers.Serializer:
    """
    Dynamically constructs a serializer class based on given properties and filters.
    """

    fields = {
        "aapp_title": serializers.CharField()
    }  # Always include title as a property

    # Add property fields
    for prop in properties:
        field_class = property_serializer_mapping.get(
            prop.get("property_type"), serializers.CharField
        )
        fields[prop["property_key"]] = field_class(allow_null=True)

    # Add filter fields (if not already included)
    for filt in filters:
        key = filt["filter_key"]
        if key not in fields:
            field_class = filter_serializer_mapping.get(
                type(filt["filter_value"]).__name__, serializers.CharField
            )
            fields[key] = field_class()

    if list_property is not None:
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
    list_property: Dict[str, Any],
) -> serializers.Serializer:
    DynamicPropertiesSerializer = build_dynamic_properties_serializer(
        properties, filters, list_property
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
    list_property: Dict[str, Any],
) -> serializers.Serializer:
    DynamicListSerializer = build_service_list_serializer(
        properties, filters, list_property
    )

    class DynamicGeoJsonSerializer(serializers.Serializer):
        type = serializers.CharField()
        features = DynamicListSerializer(many=True)

    return DynamicGeoJsonSerializer


def build_map_response_serializer(
    properties: list[Dict[str, Any]],
    filters: list[Dict[str, Any]],
    list_property: Dict[str, Any],
) -> serializers.Serializer:
    DynamicGeoJsonSerializer = build_geojson_serializer(
        properties, filters, list_property
    )

    class DynamicMapResponseSerializer(ServiceMapResponseSerializer):
        data = DynamicGeoJsonSerializer()

    return DynamicMapResponseSerializer


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
    coordinates = serializers.ListField(child=serializers.FloatField())


class ServiceListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    geometry = GeometrySerializer()
    properties = serializers.DictField()


class ServiceMapGeoJsonSerializer(serializers.Serializer):
    type = serializers.CharField()
    features = ServiceListSerializer(many=True)


class ServiceMapResponseSerializer(serializers.Serializer):
    filters = FiltersSerializer(many=True)
    properties_to_include = PropertiesSerializer(many=True)
    list_property = ListPropertySerializer(allow_null=True)
    data = ServiceMapGeoJsonSerializer()
