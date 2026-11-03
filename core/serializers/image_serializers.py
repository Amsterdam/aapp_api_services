from rest_framework import serializers


class ImageSourcesSerializer(serializers.Serializer):
    uri = serializers.CharField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()


class ImageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sources = ImageSourcesSerializer(many=True)
    alternativeText = serializers.CharField(required=False, allow_blank=True)
    alt = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
