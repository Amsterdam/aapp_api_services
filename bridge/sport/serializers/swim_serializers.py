from rest_framework import serializers

from core.serializers.address_serializers import AddressSerializer


class SwimLocationsResponseSerializer(serializers.Serializer):
    address = AddressSerializer(source="*", read_only=True)
    name = serializers.CharField()
