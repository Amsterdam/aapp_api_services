from rest_framework import serializers

FIELD_TYPE_MAPPING = {
    "bool": serializers.BooleanField,
    "float": serializers.FloatField,
    "int": serializers.IntegerField,
    "str": serializers.CharField,
    "url": serializers.URLField,
}


def build_dynamic_properties_serializer(properties, filters):
    """
    Dynamically constructs a serializer class based on given properties and filters.
    """

    fields = {}

    # Add property fields
    for prop in properties:
        field_class = FIELD_TYPE_MAPPING.get(
            prop.get("property_type"), serializers.CharField
        )
        fields[prop["property_key"]] = field_class(allow_null=True, required=False)

    # Add filter fields (if not already included)
    for filt in filters:
        key = filt["filter_key"]
        if key not in fields:
            field_class = FIELD_TYPE_MAPPING.get(
                type(filt["filter_value"]).__name__, serializers.CharField
            )
            fields[key] = field_class(allow_null=True, required=False)

    return type("DynamicPropertiesSerializer", (serializers.Serializer,), fields)


def build_service_list_serializer(properties, filters):
    DynamicPropertiesSerializer = build_dynamic_properties_serializer(
        properties, filters
    )

    class DynamicServiceListSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        geometry = GeometrySerializer()
        properties = DynamicPropertiesSerializer()

    return DynamicServiceListSerializer


def build_map_response_serializer(properties, filters):
    DynamicListSerializer = build_service_list_serializer(properties, filters)

    class DynamicMapResponseSerializer(ServiceMapResponseSerializer):
        data = DynamicListSerializer(many=True)

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


class GeometrySerializer(serializers.Serializer):
    type = serializers.CharField()
    coordinates = serializers.ListField(child=serializers.FloatField())


class ServiceListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    geometry = GeometrySerializer()
    properties = serializers.DictField()


class ServiceMapResponseSerializer(serializers.Serializer):
    filters = FiltersSerializer(many=True)
    properties_to_include = PropertiesSerializer(many=True)
    data = ServiceListSerializer(many=True)
