from rest_framework import serializers

from core.serializers.address_serializers import AddressSerializer


class PrideEventResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    website = serializers.CharField(allow_null=True)
    address = AddressSerializer()
    type = serializers.CharField()
    date_start = serializers.DateField(allow_null=True)
    date_end = serializers.DateField(allow_null=True)
    time = serializers.CharField(allow_null=True)


class PrideDateEventResponseSerializer(serializers.Serializer):
    date = serializers.DateField()
    events = PrideEventResponseSerializer(many=True)
