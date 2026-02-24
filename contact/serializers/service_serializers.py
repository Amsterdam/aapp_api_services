from rest_framework import serializers


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
    label = serializers.CharField()
    property_key = serializers.CharField()
    property_type = serializers.CharField()
    icon = serializers.CharField(allow_null=True)


class GeometrySerializer(serializers.Serializer):
    coordinates = serializers.ListField(child=serializers.FloatField())


class ToiletPropertiesSerializer(serializers.Serializer):
    name = serializers.CharField()
    open_hours = serializers.CharField(allow_null=True)
    price_per_use = serializers.FloatField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    image_url = serializers.URLField(allow_null=True)
    is_accessible = serializers.BooleanField()
    is_toilet = serializers.BooleanField()


class ToiletListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    geometry = GeometrySerializer()
    properties = ToiletPropertiesSerializer()


class ServiceMapResponseSerializer(serializers.Serializer):
    filters = FiltersSerializer(many=True)
    properties_to_include = PropertiesSerializer(many=True)


class ToiletMapResponseSerializer(ServiceMapResponseSerializer):
    data = ToiletListSerializer(many=True)
