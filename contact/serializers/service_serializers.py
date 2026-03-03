from rest_framework import serializers

FIELD_TYPE_MAPPING = {
    "boolean": serializers.BooleanField,
    "price": serializers.FloatField,
    "number": serializers.IntegerField,
    "string": serializers.CharField,
    "image": serializers.URLField,
}

# this mapping is used for filters. Their type is determined by the type of their filter_value, which can be int, str, or bool
FILTER_FIELD_TYPE_MAPPING = {
    "bool": serializers.BooleanField,
    "int": serializers.IntegerField,
    "str": serializers.CharField,
}


def build_dynamic_properties_serializer(properties, filters, list_property):
    """
    Dynamically constructs a serializer class based on given properties and filters.
    """

    fields = {
        "aapp_title": serializers.CharField()
    }  # Always include title as a property

    # Add property fields
    for prop in properties:
        field_class = FIELD_TYPE_MAPPING.get(
            prop.get("property_type"), serializers.CharField
        )
        fields[prop["property_key"]] = field_class(allow_null=True)

    # Add filter fields (if not already included)
    for filt in filters:
        key = filt["filter_key"]
        if key not in fields:
            field_class = FILTER_FIELD_TYPE_MAPPING.get(
                type(filt["filter_value"]).__name__, serializers.CharField
            )
            fields[key] = field_class()

    key = list_property["key"]
    if key not in fields:
        field_class = FIELD_TYPE_MAPPING.get(
            list_property["type"], serializers.CharField
        )
        # TODO: change required to True once addresses are added for taps
        fields[key] = field_class(allow_null=True, required=False)

    return type("DynamicPropertiesSerializer", (serializers.Serializer,), fields)


def build_service_list_serializer(properties, filters, list_property):
    DynamicPropertiesSerializer = build_dynamic_properties_serializer(
        properties, filters, list_property
    )

    class DynamicServiceListSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        geometry = GeometrySerializer()
        properties = DynamicPropertiesSerializer()

    return DynamicServiceListSerializer


def build_geojson_serializer(properties, filters, list_property):
    DynamicListSerializer = build_service_list_serializer(
        properties, filters, list_property
    )

    class DynamicGeoJsonSerializer(serializers.Serializer):
        type = serializers.CharField()
        features = DynamicListSerializer(many=True)

    return DynamicGeoJsonSerializer


def build_map_response_serializer(properties, filters, list_property):
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
    list_property = ListPropertySerializer()
    data = ServiceMapGeoJsonSerializer()
