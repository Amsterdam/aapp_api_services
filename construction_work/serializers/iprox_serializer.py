from rest_framework import serializers


class IproxImageSourceSerializer(serializers.Serializer):
    uri = serializers.CharField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()


class IproxImageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sources = IproxImageSourceSerializer(many=True)
    aspectRatio = serializers.FloatField()
    alternativeText = serializers.CharField()


class IproxProjectSectionLinkSerializer(serializers.Serializer):
    url = serializers.CharField()
    label = serializers.CharField()


class IproxProjectSectionSerializer(serializers.Serializer):
    body = serializers.CharField()
    links = IproxProjectSectionLinkSerializer(many=True)


class IproxProjectSectionsSerializer(serializers.Serializer):
    what = IproxProjectSectionSerializer()
    when = IproxProjectSectionSerializer()
    work = IproxProjectSectionSerializer()
    contact = IproxProjectSectionSerializer()


class IproxCoordinatesSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()


class IproxProjectTimelineItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    body = serializers.CharField()
    collapsed = serializers.BooleanField()


class IproxProjectTimelineSerializer(serializers.Serializer):
    title = serializers.CharField()
    intro = serializers.CharField()
    items = IproxProjectTimelineItemSerializer(many=True)


class IproxProjectContactSerializer(serializers.Serializer):
    id = serializers.FloatField()
    name = serializers.CharField()
    email = serializers.CharField()
    phone = serializers.CharField()
    position = serializers.CharField()
