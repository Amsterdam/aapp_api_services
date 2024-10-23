from rest_framework import serializers


class MetaIdSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
