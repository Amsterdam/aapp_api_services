from rest_framework import serializers

from construction_work.models.manage_models import Image


class MetaIdSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()


class ImagePublicSerializer(serializers.ModelSerializer):
    """Image public serializer"""

    uri = serializers.URLField(source="image")

    class Meta:
        model = Image
        fields = ["uri", "width", "height"]


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
    title = serializers.CharField()
    links = IproxProjectSectionLinkSerializer(many=True)


class IproxProjectSectionsSerializer(serializers.Serializer):
    what = IproxProjectSectionSerializer()
    when = IproxProjectSectionSerializer()
    work = IproxProjectSectionSerializer()
    contact = IproxProjectSectionSerializer()


class IproxCoordinatesSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()


class RecursiveField(serializers.Field):
    def to_representation(self, value):
        serializer = IproxProjectTimelineItemSerializer(
            value, many=True, context=self.context
        )
        return serializer.data


class IproxProjectTimelineItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    body = serializers.CharField()
    collapsed = serializers.BooleanField()
    items = serializers.ListField(child=RecursiveField())


class IproxProjectTimelineSerializer(serializers.Serializer):
    title = serializers.CharField()
    intro = serializers.CharField()
    items = IproxProjectTimelineItemSerializer(many=True)
