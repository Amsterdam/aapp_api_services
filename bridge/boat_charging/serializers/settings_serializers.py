from rest_framework import serializers


class SettingsResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    value = serializers.CharField()
