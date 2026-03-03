from rest_framework import serializers


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


class ToiletPropertiesSerializer(serializers.Serializer):
    # TODO: change this to dynamically generate fields based on the filters and properties when moving out of MVP stage
    aapp_title = serializers.CharField()
    aapp_opening_hours = serializers.CharField(allow_null=True)
    aapp_days_open = serializers.CharField(allow_null=True)
    Prijs_per_gebruik = serializers.FloatField(allow_null=True)
    aapp_description = serializers.CharField(allow_null=True)
    aapp_image_url = serializers.URLField(allow_null=True)
    aapp_is_accessible = serializers.BooleanField()
    aapp_is_toilet = serializers.BooleanField()


class ServiceListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    geometry = GeometrySerializer()
    properties = serializers.DictField()


class ToiletListSerializer(ServiceListSerializer):
    properties = ToiletPropertiesSerializer()


class ServiceMapGeoJsonSerializer(serializers.Serializer):
    type = serializers.CharField()
    features = ServiceListSerializer(many=True)


class ServiceMapResponseSerializer(serializers.Serializer):
    filters = FiltersSerializer(many=True)
    properties_to_include = PropertiesSerializer(many=True)
    data = ServiceMapGeoJsonSerializer()


class ToiletGeoJsonSerializer(serializers.Serializer):
    type = serializers.CharField()
    features = ToiletListSerializer(many=True)


class ToiletMapResponseSerializer(ServiceMapResponseSerializer):
    data = ToiletGeoJsonSerializer()
