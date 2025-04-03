from rest_framework import serializers


class PermitZoneRequestSerializer(serializers.Serializer):
    permit_zone = serializers.CharField()
